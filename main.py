import discord
from discord.ext import commands
from datetime import datetime
import os
import asyncio
from keep_alive import keep_alive

# Configure bot intents
intents = discord.Intents.default()
intents.message_content = True  # Required for command processing
intents.guilds = True
intents.members = True  # Optional, enable if needed for member-related features

# Initialize bot with command prefix and intents
bot = commands.Bot(command_prefix=",", intents=intents)

# Set bot owner IDs (replace with your Discord user ID)
bot.owner_ids = {1038522974988411000, 1320762191661764689}  # Add your user ID here

# Track bot uptime
bot.uptime = datetime.utcnow()

@bot.command()
async def say(ctx, *, message: str):
    try:
        await ctx.message.delete()  # Delete the command message
    except discord.Forbidden:
        pass  # If the bot can't delete the message, just ignore the error

    await ctx.send(message)
    
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user.name} ({bot.user.id})")
    print(f"Connected to {len(bot.guilds)} guilds")
    print("Bot is ready!")

async def load_extensions():
    # Load Jishaku cog
    try:
        await bot.load_extension("cogs.jishaku")
        print("Loaded Jishaku cog")
    except Exception as e:
        print(f"Failed to load Jishaku cog: {e}")

    try:
        await bot.load_extension("cogs.newspanel")
        print("Loaded News Panel cog")
    except Exception as e:
        print(f"Failed to load News Panel cog: {e}")

    try:
        await bot.load_extension("cogs.moderation")
        print("Loaded Moderation cog")
    except Exception as e:
        print(f"Failed to load Moderation cog: {e}")

    try:
        await bot.load_extension("cogs.prodpanel")
        print("Loaded Production Panel cog")
    except Exception as e:
        print(f"Failed to load Production Panel cog: {e}")

    try:
        await bot.load_extension("cogs.shrpanel")
        print("Loaded SHR Panel cog")
    except Exception as e:
        print(f"Failed to load SHR Panel cog: {e}")

    try:
        await bot.load_extension("cogs.support")
        print("Loaded Support cog")
    except Exception as e:
        print(f"Failed to load Support cog: {e}")

    try:
        await bot.load_extension("cogs.cmd")
        print("Loaded Trainings cog")
    except Exception as e:
        print(f"Failed to load CMD cog: {e}")

        
@bot.event
async def on_member_join(member: discord.Member):
    global auto_role_enabled, role_to_assign
    if auto_role_enabled and role_to_assign:
        try:
            await member.add_roles(role_to_assign)
            print(f"✅ Assigned {role_to_assign.name} to {member.name}.")
        except discord.Forbidden:
            print(f"❌ Failed to assign {role_to_assign.name} to {member.name}. Bot lacks permissions.")

# Prefix Commands
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
            await ctx.send("❌ You must **mention** a role (e.g., `,autorole on @Role`).")
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
    # Load extensions and start bot
    await load_extensions()
    
    # Replace 'YOUR_BOT_TOKEN' with your actual bot token
    keep_alive()
    await bot.start("MTM3NTk3NzI4Mjg1MzY3MTExMw.G2kgr1.ePnxWc42wSjctEYIK5fiz5FxdC3oGkOHNoKEws")

if __name__ == "__main__":
    asyncio.run(main())
