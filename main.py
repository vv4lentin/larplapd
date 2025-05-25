import discord
from discord.ext import commands
from datetime import datetime
import os
import asyncio
from keep_alive import keep_alive

ANNOUNCEMENT_CHANNEL_ID = 1292541250775290097

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

@bot.command()
async def say(ctx, *, message: str):
    try:
        await ctx.message.delete()
    except discord.Forbidden:
        pass
    await ctx.send(message)


@bot.command(name="announce")
async def announce(ctx, *, message: str):
    # Delete the user's original message
    await ctx.message.delete()

    # Get the announcement channel
    channel = bot.get_channel(ANNOUNCEMENT_CHANNEL_ID)

    if channel is None:
        await ctx.send("❌ Announcement channel not found.", delete_after=5)
        return

    # Send the message to the announcement channel
    await channel.send(message)
    
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
    try:
        await bot.load_extension("cogs.jishaku")
        print("Loaded Jishaku cog")
    except Exception as e:
        print(f"Failed to load Jishaku cog: {e}")
    try:
        await bot.load_extension("cogs.lapdmanage")
        print("Loaded LAPD Manage cog")
    except Exception as e:
        print(f"Failed to load LAPD Manage cog: {e}")
    try:
        await bot.load_extension("cogs.trainingevents")
        print("Loaded Training and Events cog")
    except Exception as e:
        print(f"Failed to load Training and Events cog: {e}")
    try:
        await bot.load_extension("cogs.support")
        print("Loaded Support cog")
    except Exception as e:
        print(f"Failed to load Support cog: {e}")
        
@bot.event
async def on_member_join(member: discord.Member):
    global auto_role_enabled, role_to_assign
    if auto_role_enabled and role_to_assign:
        try:
            await member.add_roles(role_to_assign)
            print(f"✅ Assigned {role_to_assign.name} to {member.name}.")
        except discord.Forbidden:
            print(f"❌ Failed to assign {role_to_assign.name} to {member.name}. Bot lacks permissions.")

@bot.command()
async def test(ctx):
    print("Command executed once")
    await ctx.send("Test command executed.")

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

async def main():
    await load_extensions()
    keep_alive()
    await bot.start("MTM3NTk3NzI4Mjg1MzY3MTExMw.G2kgr1.ePnxWc42wSjctEYIK5fiz5FxdC3oGkOHNoKEws")  # Replace with your token or use os.getenv('BOT_TOKEN')

if __name__ == "__main__":
    asyncio.run(main())
