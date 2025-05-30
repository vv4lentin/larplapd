import discord
from discord.ext import commands
from datetime import datetime, timedelta
import re

# Role and Channel IDs
MOD_PERMS_ROLE_ID = [1361565373593292851, 1306387524494561370]  # Role ID for permission to use mod commands
LOG_CHANNEL_ID = 1377974406277501021     # Channel ID for unauthorized access logs
ALERT_ROLE_ID = 1337050305153470574      # Role to ping for unauthorized access
OWNER_USER_ID = [1038522974988411000, 792827523858694144, 792547313716690965]     # User ID of the bot's official owner

class Mod(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def check_permissions(self, ctx: commands.Context) -> bool:
        """Check if the user has the required role."""
        return MOD_PERMS_ROLE_ID in [role.id for role in ctx.author.roles]

    async def send_unauthorized_alert(self, ctx: commands.Context):
        """Send unauthorized access message and log to the specified channel."""
        await ctx.send("Unauthorized access detected ⚠️ ! An alert has been sent to the bot tamer.")
        log_channel = self.bot.get_channel(LOG_CHANNEL_ID)
        if log_channel:
            embed = discord.Embed(
                title="Attempted use of a restricted command",
                color=discord.Color.orange(),
                timestamp=datetime.now()
            )
            embed.add_field(name="User", value=ctx.author.mention, inline=False)
            embed.add_field(name="Message", value=ctx.message.content or "No message content", inline=False)
            embed.add_field(
                name="Jump to message",
                value=f"[Click here]({ctx.message.jump_url})",
                inline=False
            )
            ping_message = f"<@&{ALERT_ROLE_ID}>"
            await log_channel.send(content=ping_message, embed=embed)
        else:
            print(f"Error: Could not find log channel with ID {LOG_CHANNEL_ID}")

    async def send_owner_protection_alert(self, ctx: commands.Context):
        """Send alert when attempting to punish the bot's owner."""
        await ctx.send("Sorry, but I can’t punish this user as he is my official owner.")
        log_channel = self.bot.get_channel(LOG_CHANNEL_ID)
        if log_channel:
            embed = discord.Embed(
                title="Attempted use of a restricted command",
                color=discord.Color.orange(),
                timestamp=datetime.now()
            )
            embed.add_field(name="User", value=ctx.author.mention, inline=False)
            embed.add_field(name="Message", value=ctx.message.content or "No message content", inline=False)
            embed.add_field(
                name="Jump to message",
                value=f"[Click here]({ctx.message.jump_url})",
                inline=False
            )
            ping_message = f"<@{OWNER_USER_ID}>"
            await log_channel.send(content=ping_message, embed=embed)
        else:
            print(f"Error: Could not find log channel with ID {LOG_CHANNEL_ID}")

    @commands.command(name="ban")
    async def ban(self, ctx: commands.Context, member: discord.Member, *, reason: str = None):
        if not self.check_permissions(ctx):
            await self.send_unauthorized_alert(ctx)
            return
        if member.id == OWNER_USER_ID:
            await self.send_owner_protection_alert(ctx)
            return
        try:
            await member.ban(reason=reason)
            embed = discord.Embed(
                title="User Banned",
                description=f"{member.mention} has been banned.",
                color=discord.Color.red(),
                timestamp=datetime.now()
            )
            embed.add_field(name="Reason", value=reason or "No reason provided", inline=False)
            embed.add_field(name="Moderator", value=ctx.author.mention, inline=False)
            await ctx.send(embed=embed)
        except discord.Forbidden:
            await ctx.send("Error: I don't have permission to ban this user.")
        except discord.HTTPException as e:
            await ctx.send(f"Error: Failed to ban user. {e}")

    @commands.command(name="kick")
    async def kick(self, ctx: commands.Context, member: discord.Member, *, reason: str = None):
        if not self.check_permissions(ctx):
            await self.send_unauthorized_alert(ctx)
            return
        if member.id == OWNER_USER_ID:
            await self.send_owner_protection_alert(ctx)
            return
        try:
            await member.kick(reason=reason)
            embed = discord.Embed(
                title="User Kicked",
                description=f"{member.mention} has been kicked.",
                color=discord.Color.red(),
                timestamp=datetime.now()
            )
            embed.add_field(name="Reason", value=reason or "No reason provided", inline=False)
            embed.add_field(name="Moderator", value=ctx.author.mention, inline=False)
            await ctx.send(embed=embed)
        except discord.Forbidden:
            await ctx.send("Error: I don't have permission to kick this user.")
        except discord.HTTPException as e:
            await ctx.send(f"Error: Failed to kick user. {e}")

    @commands.command(name="timeout")
    async def timeout(self, ctx: commands.Context, member: discord.Member, duration: str, *, reason: str = None):
        if not self.check_permissions(ctx):
            await self.send_unauthorized_alert(ctx)
            return
        if member.id == OWNER_USER_ID:
            await self.send_owner_protection_alert(ctx)
            return
        # Parse duration (e.g., 5m, 1h, 2d)
        time_units = {"s": 1, "m": 60, "h": 3600, "d": 86400}
        match = re.match(r"(\d+)([smhd])", duration.lower())
        if not match:
            await ctx.send("Error: Invalid duration format. Use something like `5m`, `1h`, or `2d`.")
            return
        amount, unit = int(match.group(1)), match.group(2)
        seconds = amount * time_units[unit]
        if seconds > 2419200:  # Discord's max timeout is 28 days
            await ctx.send("Error: Timeout duration cannot exceed 28 days.")
            return
        try:
            await member.timeout(timedelta(seconds=seconds), reason=reason)
            embed = discord.Embed(
                title="User Timed Out",
                description=f"{member.mention} has been timed out for {duration}.",
                color=discord.Color.red(),
                timestamp=datetime.now()
            )
            embed.add_field(name="Reason", value=reason or "No reason provided", inline=False)
            embed.add_field(name="Moderator", value=ctx.author.mention, inline=False)
            await ctx.send(embed=embed)
        except discord.Forbidden:
            await ctx.send("Error: I don't have permission to timeout this user.")
        except discord.HTTPException as e:
            await ctx.send(f"Error: Failed to timeout user. {e}")

    @commands.command(name="unban")
    async def unban(self, ctx: commands.Context, user_id: int, *, reason: str = None):
        if not self.check_permissions(ctx):
            await self.send_unauthorized_alert(ctx)
            return
        if user_id == OWNER_USER_ID:
            await self.send_owner_protection_alert(ctx)
            return
        try:
            user = await self.bot.fetch_user(user_id)
            await ctx.guild.unban(user, reason=reason)
            embed = discord.Embed(
                title="User Unbanned",
                description=f"{user.mention} ({user.id}) has been unbanned.",
                color=discord.Color.green(),
                timestamp=datetime.now()
            )
            embed.add_field(name="Reason", value=reason or "No reason provided", inline=False)
            embed.add_field(name="Moderator", value=ctx.author.mention, inline=False)
            await ctx.send(embed=embed)
        except discord.NotFound:
            await ctx.send("Error: User not found or not banned.")
        except discord.Forbidden:
            await ctx.send("Error: I don't have permission to unban this user.")
        except discord.HTTPException as e:
            await ctx.send(f"Error: Failed to unban user. {e}")

    @commands.command(name="untimeout")
    async def untimeout(self, ctx: commands.Context, member: discord.Member, *, reason: str = None):
        if not self.check_permissions(ctx):
            await self.send_unauthorized_alert(ctx)
            return
        if member.id == OWNER_USER_ID:
            await self.send_owner_protection_alert(ctx)
            return
        try:
            await member.timeout(None, reason=reason)
            embed = discord.Embed(
                title="User Timeout Removed",
                description=f"Timeout has been removed from {member.mention}.",
                color=discord.Color.green(),
                timestamp=datetime.now()
            )
            embed.add_field(name="Reason", value=reason or "No reason provided", inline=False)
            embed.add_field(name="Moderator", value=ctx.author.mention, inline=False)
            await ctx.send(embed=embed)
        except discord.Forbidden:
            await ctx.send("Error: I don't have permission to remove timeout from this user.")
        except discord.HTTPException as e:
            await ctx.send(f"Error: Failed to remove timeout. {e}")

async def setup(bot):
    await bot.add_cog(Mod(bot))
