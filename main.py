import discord
from discord.ext import commands
from datetime import datetime
import os
import asyncio
import json

from keep_alive import keep_alive  # Assuming this is a custom module for keeping the bot alive

ANNOUNCEMENT_CHANNEL_ID = 1292541250775290097
ALLOWED_ROLE_IDS = [1337050305153470574, 1361565373593292851]

# Configure bot intents
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True
intents.presences = True  # Presence intent for status changes

# Initialize bot with command prefix and intents
bot = commands.Bot(command_prefix="!", intents=intents)

# Initialize global variables
auto_role_enabled = False
role_to_assign = None
sleep_mode = False  # Global flag for sleep mode
loaded_cogs = []  # Added to track successfully loaded cogs

# Track bot uptime
bot.uptime = datetime.utcnow()

# Global check to block commands when in sleep mode
@bot.check
async def block_commands_in_sleep_mode(ctx):
    if not sleep_mode:
        return True  # Allow commands if not in sleep mode
    if ctx.command.name == "start" and await bot.is_owner(ctx.author):
        return True  # Allow !start for bot owner
    # Create embed for sleep mode response
    embed = discord.Embed(
        title="Bot is in sleep mode.",
        description="Bot is in sleep mode, all commands are unavailable, please contact the bot developer so he can start it.",
        color=discord.Color.red()
    )
    embed.set_footer(text=f"Command used: {ctx.command.name} | User ID: {ctx.author.id}")
    await ctx.send(embed=embed)
    return False  # Block all other commands

@bot.command()
async def say(ctx, *, message: str):
    try:
        await ctx.message.delete()
        await ctx.send(message)
    except discord.Forbidden:
        await ctx.send("❌ I don't have permission to delete messages.", delete_after=5)

@bot.command(name="announce")
async def announce(ctx, *, message: str):
    # Check if the user has one of the allowed roles
    if not any(role.id in ALLOWED_ROLE_IDS for role in ctx.author.roles):
        try:
            await ctx.message.delete()
            await ctx.author.send("This is a restricted command, only Bot Tamers and Board of Chiefs members can use it.")
        except discord.Forbidden:
            pass  # Silently fail if bot can't DM user
        return

    try:
        await ctx.message.delete()
    except discord.Forbidden:
        pass

    # Get the announcement channel
    channel = bot.get_channel(ANNOUNCEMENT_CHANNEL_ID)
    if channel is None:
        await ctx.author.send(f"❌ Announcement channel with ID {ANNOUNCEMENT_CHANNEL_ID} not found.")
        return

    try:
        await channel.send(message)
        await ctx.author.send(f"✅ Announcement sent to {channel.mention}.")
    except discord.Forbidden:
        await ctx.author.send(f"❌ I don't have permission to send messages in {channel.mention}.")

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
        print(f"Failed to sync commands to guild: {e}")

async def load_extensions():
    global loaded_cogs  # Added to modify global list
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
            print(f"Loaded {cog} cog")
            loaded_cogs.append(cog.split(".")[-1])  # Add cog name to loaded_cogs (e.g., "jishaku")
        except Exception as e:
            print(f"Failed to load {cog} cog: {e}")

@bot.event
async def on_member_join(member: discord.Member):
    global auto_role_enabled, role_to_assign
    if auto_role_enabled and role_to_assign:
        try:
            await member.add_roles(role_to_assign)
            print(f"✅ Assigned {role_to_assign.name} to {member.name}.")
        except discord.Forbidden:
            print(f"❌ Failed to assign {role_to_assign.name} to {member.name}. Bot lacks permissions.")
        except discord.HTTPException as e:
            print(f"❌ Failed to assign role: {e}")

@bot.command()
async def test(ctx):
    print("Command executed once")
    await ctx.send("Test command executed.")

@bot.command()
async def dumb(ctx):
    await ctx.send("Yeah I think we all know that we are talking about <@1320762191661764689>")
    await asyncio.sleep(1)  # Added delay to prevent rate-limiting
    await ctx.send("I ping another time maybe he didn't understand <@1320762191661764689>.")
    await asyncio.sleep(1)
    await ctx.send("Maybe a last time to make sure that he understand that he is the dumbest of the department <@1320762191661764689>.")

@bot.command(name='purge')
@commands.has_permissions(manage_messages=True)
@commands.bot_has_permissions(manage_messages=True)
async def purge(ctx, amount: int):
    if amount < 1 or amount > 100:
        await ctx.send("Please specify a number between 1 and 100.", delete_after=5)
        return
    try:
        await ctx.channel.purge(limit=amount + 1)
        await ctx.send(f"Successfully deleted {amount} message(s).", delete_after=5)
    except discord.Forbidden:
        await ctx.send("❌ I don't have permission to delete messages.", delete_after=5)
    except discord.HTTPException as e:
        await ctx.send(f"❌ Failed to purge messages: {e}", delete_after=5)

@purge.error
async def purge_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("You need 'Manage Messages' permission.", delete_after=5)
    elif isinstance(error, commands.BotMissingPermissions):
        await ctx.send("I need 'Manage Messages' permission.", delete_after=5)
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("Please specify the number of messages to purge.", delete_after=5)
    elif isinstance(error, commands.CheckFailure):
        return  # Handled by globally_block_banned_users or sleep mode check
    else:
        print(f"Purge error: {error}")
        await ctx.send(f"Error: {str(error)}", delete_after=5)

@bot.command()
async def hello(ctx):
    await ctx.send("You thought I would say hello didn't you, bitch?")

@bot.command()
async def autorole(ctx, status: str, role: discord.Role = None):
    global auto_role_enabled, role_to_assign
    if status.lower() == "on":
        if role:
            role_to_assign = role
            auto_role_enabled = True
            await ctx.send(f"✅ Auto-role is now **ON**. The role {role.mention} will be assigned to all new members.")
        else:
            await ctx.send("❌ You must **mention** a role (e.g., `!autorole on @Role`).")
    elif status.lower() == "off":
        auto_role_enabled = False
        role_to_assign = None
        await ctx.send("🚫 Auto-role is now **OFF**.")
    else:
        await ctx.send("❌ Please specify either `on` or `off`.")

@bot.command()
async def currentautorole(ctx):
    global auto_role_enabled, role_to_assign
    if auto_role_enabled and role_to_assign:
        await ctx.send(f"✅ Auto-role is **ON**. The assigned role is {role_to_assign.mention}.")
    else:
        await ctx.send("🚫 Auto-role is **OFF**.")

@bot.command()
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
        await ctx.send("❌ I don't have permission to change this member's nickname.", delete_after=5)
    except discord.HTTPException as e:
        await ctx.send(f"❌ Failed to change nickname: {e}", delete_after=5)

@bot.command()
@commands.is_owner()  # Restricts command to bot owner
async def stop(ctx):
    """Puts the bot in sleep mode."""
    global sleep_mode
    try:
        # Set activity to "Waiting for developers to start me.." and status to idle
        activity = discord.Activity(
            type=discord.ActivityType.playing,
            name="Waiting for developers to start me.."
        )
        await bot.change_presence(status=discord.Status.idle, activity=activity)
        sleep_mode = True  # Enable sleep mode
        # Upgraded embed with timestamp and cog list
        embed = discord.Embed(
            title="Bot Entering Sleep Mode",
            description="The bot is now in sleep mode. All commands are disabled until reactivated.",
            color=discord.Color.red(),
            timestamp=datetime.utcnow()
        )
        # List all loaded cogs
        cogs_list = loaded_cogs if loaded_cogs else ["None"]
        embed.add_field(
            name="Disabled Cogs",
            value=", ".join(cogs_list),
            inline=False
        )
        embed.set_footer(text=f"Command used: stop | User ID: {ctx.author.id}")
        await ctx.send(embed=embed)
    except Exception as e:
        await ctx.send(f"Error setting sleep mode: {e}")

@bot.command()
@commands.is_owner()  # Restricts command to bot owner
async def start(ctx):
    """Activates the bot."""
    global sleep_mode
    try:
        # Set activity to "Watching Los Angeles Police Department" and status to DND
        activity = discord.Activity(
            type=discord.ActivityType.watching,
            name="Los Angeles Police Department"
        )
        await bot.change_presence(status=discord.Status.dnd, activity=activity)
        sleep_mode = False  # Disable sleep mode
        # Upgraded embed with timestamp and cog list
        embed = discord.Embed(
            title="Bot Activated",
            description="The bot is now active and all commands are available.",
            color=discord.Color.green(),
            timestamp=datetime.utcnow()
        )
        # List all loaded cogs
        cogs_list = loaded_cogs if loaded_cogs else ["None"]
        embed.add_field(
            name="Enabled Cogs",
            value=", ".join(cogs_list),
            inline=False
        )
        embed.set_footer(text=f"Command used: start | User ID: {ctx.author.id}")
        await ctx.send(embed=embed)
    except Exception as e:
        await ctx.send(f"Error activating bot: {e}")

async def main():
    await load_extensions()
    keep_alive()  # Ensure this function is properly defined in keep_alive.py
    try:
        await bot.start(os.getenv("BOT_TOKEN") or "MTM3NTk3NzI4Mjg1MzY3MTExMw.GsT2gi.9KQThQd57nEbRNHm1bEO2uOoE1BnAydsDiqjWA")
    except Exception as e:
        print(f"Failed to start bot: {e}")

if __name__ == "__main__":
    asyncio.run(main())
