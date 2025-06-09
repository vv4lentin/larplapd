import discord
from discord.ext import commands
from datetime import datetime
import os
import asyncio
import json
from keep_alive import keep_alive  # Custom module to keep the bot running

# Configuration
ANNOUNCEMENT_CHANNEL_ID = 1292541250775290097
ALLOWED_ROLE_IDS = [1337050305153470574, 1361565373593292851]
BOT_TOKEN = "MTM3NTk3NzI4Mjg1MzY3MTExMw.GsT2gi.9KQThQd57nEbRNHm1bEO2uOoE1BnAydsDiqjWA"  # WARNING: Hardcoding tokens is insecure! Use environment variables in production.

# Load banned users from JSON file
def load_banned_users():
    ban_file = "banned_users.json"
    if os.path.exists(ban_file):
        try:
            with open(ban_file, 'r') as f:
                content = f.read().strip()
                if not content:
                    return {}
                return json.loads(content)
        except json.JSONDecodeError as e:
            print(f"Warning: {ban_file} contains invalid JSON: {e}. Initializing with empty dictionary.")
            return {}
    return {}

# Configure bot intents
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True
intents.presences = True

# Initialize bot
bot = commands.Bot(command_prefix="!", intents=intents, case_insensitive=True)

# Global variables
auto_role_enabled = False
role_to_assign = None
sleep_mode = False
loaded_cogs = []
bot.uptime = datetime.utcnow()

# Global check to block banned users
@bot.check
async def globally_block_banned_users(ctx):
    banned_users = load_banned_users()
    if str(ctx.author.id) in banned_users:
        embed = discord.Embed(
            title="Command Access Denied",
            description="You are banned from using bot commands.",
            color=discord.Color.red(),
            timestamp=datetime.utcnow()
        )
        embed.set_footer(text=f"User ID: {ctx.author.id}")
        await ctx.send(embed=embed, delete_after=10)
        return False
    return True

# Global check for sleep mode
@bot.check
async def block_commands_in_sleep_mode(ctx):
    if not sleep_mode:
        return True
    if ctx.command.name == "start" and await bot.is_owner(ctx.author):
        return True
    embed = discord.Embed(
        title="Bot in Sleep Mode",
        description="All commands are disabled. Contact the bot developer to reactivate.",
        color=discord.Color.red(),
        timestamp=datetime.utcnow()
    )
    embed.set_footer(text=f"Command: {ctx.command.name} | User ID: {ctx.author.id}")
    await ctx.send(embed=embed, delete_after=10)
    return False

# Basic commands
@bot.command()
async def say(ctx, *, message: str):
    try:
        await ctx.message.delete()
        await ctx.send(message)
    except discord.Forbidden:
        await ctx.send("❌ I lack permission to delete messages.", delete_after=5)
    except discord.HTTPException as e:
        await ctx.send(f"❌ Failed to send message: {e}", delete_after=5)

@bot.command(name="announce")
async def announce(ctx, *, message: str):
    if not any(role.id in ALLOWED_ROLE_IDS for role in ctx.author.roles):
        try:
            await ctx.message.delete()
            await ctx.author.send("❌ This command is restricted to Bot Tamers and Board of Chiefs members.")
        except discord.Forbidden:
            pass
        return

    try:
        await ctx.message.delete()
    except discord.Forbidden:
        pass

    channel = bot.get_channel(ANNOUNCEMENT_CHANNEL_ID)
    if channel is None:
        await ctx.author.send(f"❌ Announcement channel (ID: {ANNOUNCEMENT_CHANNEL_ID}) not found.")
        return

    try:
        await channel.send(message)
        await ctx.author.send(f"✅ Announcement sent to {channel.mention}.")
    except discord.Forbidden:
        await ctx.author.send(f"❌ I lack permission to send messages in {channel.mention}.")
    except discord.HTTPException as e:
        await ctx.author.send(f"❌ Failed to send announcement: {e}")

# Bot events
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user.name} ({bot.user.id})")
    print(f"Connected to {len(bot.guilds)} guilds")
    print("Bot is ready!")
    try:
        guild = discord.Object(id=1292523481539543193)
        synced = await bot.tree.sync(guild=guild)
        print(f"Synced {len(synced)} command(s) to guild {guild.id}")
    except Exception as e:
        print(f"Failed to sync commands: {e}")

@bot.event
async def on_member_join(member: discord.Member):
    global auto_role_enabled, role_to_assign
    if auto_role_enabled and role_to_assign:
        try:
            await member.add_roles(role_to_assign)
            print(f"✅ Assigned {role_to_assign.name} to {member.name}.")
        except discord.Forbidden:
            print(f"❌ Failed to assign {role_to_assign.name} to {member.name}: Missing permissions.")
        except discord.HTTPException as e:
            print(f"❌ Failed to assign role: {e}")

# Load cogs
async def load_extensions():
    global loaded_cogs
    cogs = [
        "cogs.jishaku",
        "cogs.lapdmanage",
        "cogs.trainingevents",
        "cogs.support",
        "cogs.mod",
        "cogs.lapd",
        "cogs.bot",
        "cogs.swatmanage",
        "cogs.embedbuilder",
        "cogs.panel",
        "cogs.commandsban"
    ]
    for cog in cogs:
        try:
            await bot.load_extension(cog)
            cog_name = cog.split(".")[-1]
            loaded_cogs.append(cog_name)
            print(f"Loaded cog: {cog_name}")
        except Exception as e:
            print(f"Failed to load cog {cog}: {e}")

# Additional commands
@bot.command()
async def test(ctx):
    print("Test command executed")
    await ctx.send("Test command executed successfully.")

@bot.command()
async def dumb(ctx):
    target = "<@1320762191661764689>"
    messages = [
        f"Yeah, we all know we're talking about {target}.",
        f"Maybe he didn't get it, let's ping again: {target}.",
        f"One last time to make sure he knows he's the dumbest in the department: {target}."
    ]
    for msg in messages:
        await ctx.send(msg)
        await asyncio.sleep(2)  # Increased delay to avoid rate limits

@bot.command(name="purge")
@commands.has_permissions(manage_messages=True)
@commands.bot_has_permissions(manage_messages=True)
async def purge(ctx, amount: int):
    if not 1 <= amount <= 100:
        await ctx.send("Please specify a number between 1 and 100.", delete_after=5)
        return
    try:
        await ctx.channel.purge(limit=amount + 1)
        await ctx.send(f"✅ Successfully deleted {amount} message(s).", delete_after=5)
    except discord.Forbidden:
        await ctx.send("❌ I lack permission to delete messages.", delete_after=5)
    except discord.HTTPException as e:
        await ctx.send(f"❌ Failed to purge messages: {e}", delete_after=5)

@purge.error
async def purge_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ You need 'Manage Messages' permission.", delete_after=5)
    elif isinstance(error, commands.BotMissingPermissions):
        await ctx.send("❌ I need 'Manage Messages' permission.", delete_after=5)
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("❌ Please specify the number of messages to purge.", delete_after=5)
    elif isinstance(error, commands.CheckFailure):
        return  # Handled by global checks
    else:
        print(f"Purge error: {error}")
        await ctx.send(f"❌ Error: {str(error)}", delete_after=5)

@bot.command()
async def hello(ctx):
    await ctx.send("You thought I'd say hello? Think again!")

@bot.command()
@commands.has_permissions(manage_roles=True)
async def autorole(ctx, status: str, role: discord.Role = None):
    global auto_role_enabled, role_to_assign
    status = status.lower()
    if status == "on":
        if not role:
            await ctx.send("❌ You must mention a role (e.g., `!autorole on @Role`).")
            return
        auto_role_enabled = True
        role_to_assign = role
        await ctx.send(f"✅ Auto-role is **ON**. New members will receive {role.mention}.")
    elif status == "off":
        auto_role_enabled = False
        role_to_assign = None
        await ctx.send("🚫 Auto-role is **OFF**.")
    else:
        await ctx.send("❌ Please specify 'on' or 'off'.")

@bot.command()
async def currentautorole(ctx):
    global auto_role_enabled, role_to_assign
    if auto_role_enabled and role_to_assign:
        await ctx.send(f"✅ Auto-role is **ON**. Assigned role: {role_to_assign.mention}.")
    else:
        await ctx.send("🚫 Auto-role is **OFF**.")

@bot.command()
@commands.has_permissions(manage_nicknames=True)
async def nick(ctx, member: discord.Member, *, nickname: str = None):
    try:
        await ctx.message.delete()
        old_nick = member.nick or member.name
        await member.edit(nick=nickname)
        if nickname:
            await ctx.send(f"✅ Changed {member.mention}'s nickname from '{old_nick}' to '{nickname}'.")
        else:
            await ctx.send(f"✅ Reset {member.mention}'s nickname to default.")
    except discord.Forbidden:
        await ctx.send("❌ I lack permission to change this member's nickname.", delete_after=5)
    except discord.HTTPException as e:
        await ctx.send(f"❌ Failed to change nickname: {e}", delete_after=5)

@bot.command()
@commands.is_owner()
async def stop(ctx):
    global sleep_mode
    try:
        activity = discord.Activity(type=discord.ActivityType.playing, name="Waiting for developers to start me...")
        await bot.change_presence(status=discord.Status.idle, activity=activity)
        sleep_mode = True
        embed = discord.Embed(
            title="Bot Entering Sleep Mode",
            description="All commands are disabled until reactivated.",
            color=discord.Color.red(),
            timestamp=datetime.utcnow()
        )
        embed.add_field(name="Loaded Cogs", value=", ".join(loaded_cogs) or "None", inline=False)
        embed.set_footer(text=f"Command: stop | User ID: {ctx.author.id}")
        await ctx.send(embed=embed)
    except Exception as e:
        await ctx.send(f"❌ Error setting sleep mode: {e}", delete_after=5)

@bot.command()
@commands.is_owner()
async def start(ctx):
    global sleep_mode
    try:
        activity = discord.Activity(type=discord.ActivityType.watching, name="Los Angeles Police Department")
        await bot.change_presence(status=discord.Status.dnd, activity=activity)
        sleep_mode = False
        embed = discord.Embed(
            title="Bot Activated",
            description="All commands are now available.",
            color=.discord.Color.green(),
            timestamp=datetime.utcnow()
        )
        embed.add_field(name="Loaded Cogs", value=", ".join(loaded_cogs) or "None", inline=False)
        embed.set_footer(text=f"Command: start | User ID: {ctx.author.id}")
        await ctx.send(embed=embed)
    except Exception as e:
        await ctx.send(f"❌ Error activating bot: {e}", delete_after=5)

# Main function to start the bot
async def main():
    await load_extensions()
    keep_alive()  # Ensure this function is defined in keep_alive.py
    try:
        await bot.start(BOT_TOKEN)
    except Exception as e:
        print(f"Failed to start bot: {e}")

if __name__ == "__main__":
    asyncio.run(main())
