import discord
from discord.ext import commands
from datetime import datetime
import os
import asyncio
import json
import keep_alive 
import time
import re 
from collections import Counter 
from keep_alive import keep_alive

ANNOUNCEMENT_CHANNEL_ID = 1292541250775290097
ALLOWED_ROLE_IDS = [1337050305153470574, 1361565373593292851]
HR_ROLE_IDS = [1324522426771443813, 1339058176003407915]
AUTOROLE_ROLE_ID = 1292541718033596558
DISRESPECTFUL_WORDS = [
    "idiot", "dumb", "stupid", "loser", "clown", "moron", "retard", "fool", "airhead", "pea-brain",
    "shut up", "fuck you", "screw you", "go to hell", "no one likes you", "kill yourself", "kys",
    "drop dead", "get lost", "die in a fire", "i hate you", "nobody cares", "i’ll kill you", "choke",
    "you’re worthless", "waste of space", "useless", "you suck", "worthless", "unwanted", "irrelevant",
    "bitch", "bastard", "asshole", "prick", "dickhead", "shithead", "fucker", "cunt", "whore", "slut",
    "fat", "ugly", "disgusting", "gross", "pig", "cow", "elephant", "nasty looking",
    "nigger", "nigga", "fag", "faggot", "tranny", "chink", "spic", "dyke", "kike",
    "cry about it", "stay mad", "cope", "seethe", "bozo", "ratio", "you’re crazy", "you imagined it",
    "stop overreacting", "kill urself", "smd", "your life sucks", "ur a joke", "no friends", "you’re trash"
]

CHANNEL_WHITELIST = [
    1292544200822493255,
    1292544821688537158,
    1292537114524913665,
    1348405434905530420
]

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True
intents.presences = True 

bot = commands.Bot(command_prefix="!", intents=intents)

auto_role_enabled = True
role_to_assign = AUTOROLE_ROLE_ID
sleep_mode = True 
loaded_cogs = []

bot.uptime = datetime.utcnow()

def detect_behavior_issues(content: str) -> list:
    flags = []

    if len(content) > 8 and content.upper() == content and content.isalpha():
        flags.append("🔊 Excessive yelling (ALL CAPS)")

    if re.search(r"(.)\1{5,}", content):
        flags.append("🔁 Repeated characters")

    word_counts = Counter(content.lower().split())
    if any(count >= 5 for count in word_counts.values()):
        flags.append("🔁 Word spam")

    aggressive_patterns = [
        r"\bi(?:'|’)ll kill you\b", r"\bi hate you\b", r"\byou should die\b",
        r"\bkill yourself\b", r"\bdrop dead\b", r"\byou're worthless\b",
        r"\byou’re trash\b", r"\bno one likes you\b"
    ]
    for pattern in aggressive_patterns:
        if re.search(pattern, content.lower()):
            flags.append("😡 Aggressive intent")
            break

    return flags

@bot.check
async def block_commands_in_sleep_mode(ctx):
    if await bot.is_owner(ctx.author):
        return True  # Bot owner can use all commands regardless of sleep mode
    if not sleep_mode:
        return True 
    if ctx.command.name == "start":
        return True  # Allow start command for non-owners
    embed = discord.Embed(
        title="Bot is in sleep mode.",
        description="Bot is in sleep mode, all commands are unavailable except for the bot owner. Please contact the bot developer to start it.",
        color=discord.Color.red()
    )
    embed.set_footer(text=f"Command used: {ctx.command.name} | User ID: {ctx.author.id}")
    await ctx.send(embed=embed)
    return False 

from discord import Embed, Colour

@bot.command()
async def say(ctx, *, message: str):
    allowed_user_id = 1335497299773620287
    banned_user_id = 1030197824702398547
    
    if ctx.author.id == banned_user_id:
        embed = Embed(
            title="UNAUTHORIZED",
            description=f"Hello <@{banned_user_id}>, you have been banned from using this command, and dont you dare ping and beg me again to unban./n **Reason** Self Explanatory : 'There are only 2 genders, Men and woman, *cry about it*'",
            colour=Colour.red()
        )
        embed.set_footer(text="Los Angeles Police Department")
        await ctx.send(embed=embed)
        return
    
    if ctx.author.id == allowed_user_id or any(role.id in HR_ROLE_IDS for role in ctx.author.roles):
        try:
            await ctx.message.delete()
            await ctx.send(message)
        except discord.Forbidden:
            await ctx.send("❌ I don't have permission to delete messages.", delete_after=5)
    else:
        await ctx.send("❌ You don't have the required role or permission to use this command.", delete_after=5)

@bot.command(name="announce")
async def announce(ctx, *, message: str):
    if not any(role.id in ALLOWED_ROLE_IDS for role in ctx.author.roles):
        try:
            await ctx.message.delete()
            await ctx.author.send("This is a restricted command, only Bot Tamers and Board of Chiefs members can use it.")
        except discord.Forbidden:
            pass  
        return

    try:
        await ctx.message.delete()
    except discord.Forbidden:
        pass

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
        activity = discord.Activity(
            type=discord.ActivityType.playing,
            name="Waiting for developers to start me.."
        )
        await bot.change_presence(status=discord.Status.idle, activity=activity)
        guild = discord.Object(id=1292523481539543193)
        synced = await bot.tree.sync(guild=guild)
        print(f"Synced {len(synced)} command(s) to guild {guild.id}")
    except Exception as e:
        print(f"Failed to sync commands to guild: {e}")

async def load_extensions():
    global loaded_cogs
    cogs = [
        "cogs.jishaku",
        "cogs.trainingevents",
        "cogs.support",
        "cogs.lapd",
        "cogs.embedbuilder",
        "cogs.panel",
        "cogs.certification_requests",
        "cogs.shift",
        "cogs.assignto"
    ]
    for cog in cogs:
        try:
            await bot.load_extension(cog)
            print(f"Loaded {cog} cog")
            loaded_cogs.append(cog.split(".")[-1])
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
async def searchd(ctx, user_id: int):
    await ctx.message.delete()
    author = ctx.author
    guild = ctx.guild

    target = guild.get_member(user_id)
    if not target:
        await author.send(f"❌ User with ID `{user_id}` not found in this server.")
        return

    status_msg = await author.send(embed=discord.Embed(
        title="🔍 Toxicity Scan Started",
        description=f"Scanning messages from **{target.mention}** (`{target.id}`)...\n\nPlease wait...",
        color=discord.Color.blurple()
    ))

    total_found = 0
    critical_hits = 0
    messages_scanned = 0
    messages_to_scan = 0
    flagged = []

    # Estimate total messages
    for channel_id in CHANNEL_WHITELIST:
        channel = guild.get_channel(channel_id)
        if not channel:
            continue
        try:
            messages_to_scan += sum(1 async for _ in channel.history(limit=400))
        except discord.Forbidden:
            continue

    start_time = time.time()
    last_update = start_time

    for channel_id in CHANNEL_WHITELIST:
        channel = guild.get_channel(channel_id)
        if not channel or not channel.permissions_for(guild.me).read_message_history:
            continue

        try:
            async for message in channel.history(limit=400):
                if message.author.id != user_id or not message.content:
                    continue

                messages_scanned += 1
                content = message.content.lower()
                matched_words = [w for w in DISRESPECTFUL_WORDS if w in content]
                behavior_flags = detect_behavior_issues(message.content)

                score = len(matched_words) + len(behavior_flags)
                if score == 0:
                    continue

                severity = "⚪ Low"
                color = discord.Color.green()
                if score >= 3:
                    severity = "🟠 Medium"
                    color = discord.Color.orange()
                if score >= 5:
                    severity = "🔴 High"
                    color = discord.Color.red()
                    critical_hits += 1
                if score >= 7:
                    severity = "🟥 Critical"
                    color = discord.Color.dark_red()

                embed = discord.Embed(
                    title=f"{severity} Risk Message",
                    description=message.content,
                    color=color,
                    timestamp=message.created_at.replace(tzinfo=timezone.utc)
                )
                embed.add_field(name="Channel", value=f"#{channel.name}", inline=True)
                embed.add_field(name="Message Link", value=f"[Jump to Message]({message.jump_url})", inline=False)
                if matched_words:
                    embed.add_field(name="Disrespect Terms", value=", ".join(set(matched_words)), inline=False)
                if behavior_flags:
                    embed.add_field(name="Behavior Flags", value="\n".join(behavior_flags), inline=False)
                embed.set_footer(text=f"{message.author} | ID: {message.author.id}")

                flagged.append(embed)
                total_found += 1

                # Every 10 seconds, update progress
                if time.time() - last_update >= 10:
                    elapsed = time.time() - start_time
                    rate = messages_scanned / elapsed if elapsed > 0 else 0
                    remaining = messages_to_scan - messages_scanned
                    eta = int(remaining / rate) if rate > 0 else -1
                    eta_display = f"{eta} seconds" if eta > 0 else "Calculating..."

                    await status_msg.edit(embed=discord.Embed(
                        title="🔄 Scan in Progress",
                        description=(
                            f"Scanned: `{messages_scanned}/{messages_to_scan}` messages\n"
                            f"Detected: `{total_found}` flagged messages\n"
                            f"⏳ ETA: **{eta_display}**"
                        ),
                        color=discord.Color.gold()
                    ))
                    last_update = time.time()

        except discord.Forbidden:
            continue

    # Send flagged messages
    for embed in flagged:
        await author.send(embed=embed)

    elapsed = time.time() - start_time

    # Final summary
    summary = discord.Embed(
        title="📊 Scan Summary",
        color=discord.Color.blue(),
        description=(
            f"✅ **Finished in {round(elapsed, 1)} seconds**\n"
            f"📄 Messages Scanned: `{messages_scanned}`\n"
            f"🚩 Toxic Messages: `{total_found}`\n"
            f"🔥 Critical Messages: `{critical_hits}`"
        )
    )
    if critical_hits >= 3:
        summary.add_field(
            name="🚨 Recommendation",
            value="This user shows repeated toxic behavior. Consider staff review.",
            inline=False
        )
    await author.send(embed=summary)
    
@bot.command()
async def test(ctx):
    print("Command executed once")
    await ctx.send("Test command executed.")

@bot.command()
async def dumb(ctx):
    await ctx.send("<@1320762191661764689> shush")
    await ctx.send("<@1320762191661764689> erm why u so dumb")
    await ctx.send("<@1320762191661764689> erm")

@bot.command(name='purge')
@commands.has_permissions(manage_messages=True)
@commands.bot_has_permissions(manage_messages=True)
async def purge(ctx, amount: int):
    if amount < 1 or amount > 100:
        await ctx.send("Please specify a number between 1 and 100.", delete_after=5)
        return
    try:
        # Purge only non-pinned messages
        await ctx.channel.purge(
            limit=amount + 1,
            check=lambda m: not m.pinned  # Only delete messages that are not pinned
        )
        await ctx.send(f"Successfully deleted {amount} non-pinned message(s).", delete_after=5)
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
@commands.is_owner()
async def stop(ctx):
    global sleep_mode
    try:
        activity = discord.Activity(
            type=discord.ActivityType.playing,
            name="Waiting for developers to start me.."
        )
        await bot.change_presence(status=discord.Status.idle, activity=activity)
        sleep_mode = True
        embed = discord.Embed(
            title="Bot Entering Sleep Mode",
            description="The bot is now in sleep mode. All commands are disabled except for the bot owner.",
            color=discord.Color.red(),
            timestamp=datetime.utcnow()
        )
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
@commands.is_owner()
async def start(ctx):
    global sleep_mode
    try:
        activity = discord.Activity(
            type=discord.ActivityType.watching,
            name="Los Angeles Police Department"
        )
        await bot.change_presence(status=discord.Status.dnd, activity=activity)
        sleep_mode = False
        embed = discord.Embed(
            title="Bot Activated",
            description="The bot is now active and all commands are available.",
            color=discord.Color.green(),
            timestamp=datetime.utcnow()
        )
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
    keep_alive()
    try:
        await bot.start(os.getenv("BOT_TOKEN") or "MTM3NTk3NzI4Mjg1MzY3MTExMw.GsT2gi.9KQThQd57nEbRNHm1bEO2uOoE1BnAydsDiqjWA")
    except Exception as e:
        print(f"Failed to start bot: {e}")

if __name__ == "__main__":
    asyncio.run(main())
