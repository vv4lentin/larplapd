import discord
from discord.ext import commands
from datetime import datetime
import os
import asyncio
import json  # Added missing import for JSON handling
from keep_alive import keep_alive  # Assuming this is a custom module for keeping the bot alive

ANNOUNCEMENT_CHANNEL_ID = 1292541250775290097
ALLOWED_ROLE_IDS = [1337050305153470574, 1361565373593292851]

# Configure bot intents
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

# Initialize bot with command prefix and intents
bot = commands.Bot(command_prefix="!", intents=intents)

# Initialize global variables
auto_role_enabled = False
role_to_assign = None

# Track bot uptime
bot.uptime = datetime.utcnow()

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

# Global check to block banned users from using any command
@bot.check
async def globally_block_banned_users(ctx):
    banned_users = load_banned_users()
    if str(ctx.author.id) in banned_users:
        embed = discord.Embed(
            title="Command Access Denied",
            description="You are banned from using bot commands.",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed, delete_after=5)  # Added delete_after for cleaner channels
        return False
    return True

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
    extensions = [
        "cogs.jishaku",
        "cogs.lapdmanage",
        "cogs.trainingevents",
        "cogs.support",
        "cogs.mod",
        "cogs.lapd",
        "cogs.bot",
        "cogs.panel",
        "cogs.commandsban",
    ]
    for ext in extensions:
        try:
            await bot.load_extension(ext)
            print(f"Loaded {ext} cog")
        except Exception as e:
            print(f"Failed to load {ext} cog: {e}")

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
        return  # Handled by globally_block_banned_users
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

async def main():
    await load_extensions()
    keep_alive()  # Ensure this function is properly defined in keep_alive.py
    try:
        await bot.start(os.getenv("BOT_TOKEN") or ("MTM3NTk3NzI4Mjg1MzY3MTExMw.GsT2gi.9KQThQd57nEbRNHm1bEO2uOoE1BnAydsDiqjWA"))
    except Exception as e:
        print(f"Failed to start bot: {e}")

if __name__ == "__main__":
    asyncio.run(main())
