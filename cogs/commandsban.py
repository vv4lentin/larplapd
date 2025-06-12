import discord
from discord.ext import commands
import json
import os

class CommandsBan(commands.Cog):
    def __init__(self, bot):Add commentMore actions
        self.bot = bot
        self.ban_file = "banned_users.json"
        self.banned_users = self.load_banned_users()

    def load_banned_users(self):
        """Load banned users from the JSON file, handling empty or missing files."""
        if os.path.exists(self.ban_file):
            try:
                with open(self.ban_file, 'r') as f:
                    content = f.read().strip()
                    if not content:
                        return {}
                    return json.load(f)
            except json.JSONDecodeError:
                print(f"Warning: {self.ban_file} contains invalid JSON. Initializing with empty dictionary.")
                return {}
        return {}

    def save_banned_users(self):
        """Save banned users to the JSON file."""
        with open(self.ban_file, 'w') as f:
            json.dump(self.banned_users, f, indent=4)

    def get_guilds_list(self):
        """Get a list of guild names where the bot is active."""
        guilds = [guild.name for guild in self.bot.guilds]
        return ", ".join(guilds) if guilds else "No guilds found"

    async def cog_check(self, ctx):
        """Check if the user is banned from using commands."""
        if str(ctx.author.id) in self.banned_users:
            embed = discord.Embed(
                title="Command Access Denied",
                description="You are banned from using bot commands.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return False
        return True

    @commands.group(name="cmd", invoke_without_command=True)
    async def cmd(self, ctx):
        """Base command for command ban management."""
        embed = discord.Embed(
            title="Commands Ban Help",
            description="Available subcommands: `gban`, `ungban`, `list`, `status`",
            color=discord.Color.blue()
        )
        await ctx.send(embed=embed)

    @cmd.command(name="gban")
    @commands.has_permissions(administrator=True)
    async def gban(self, ctx, user: discord.User, *, reason: str = "No reason provided"):
        """Ban a user from using bot commands."""
        if str(user.id) in self.banned_users:
            embed = discord.Embed(
                title="Commands Global Ban - Failed",
                description=f"{user.mention} is already banned from using bot commands.",
                color=discord.Color.red()
            )
            embed.add_field(name="User", value=user.name, inline=True)
            embed.add_field(name="User ID", value=user.id, inline=True)
            embed.add_field(name="Reason", value=self.banned_users[str(user.id)]["reason"], inline=True)
            embed.add_field(name="Command banned in", value=self.get_guilds_list(), inline=False)
            embed.add_field(name="Issued by", value=self.banned_users[str(user.id)]["banned_by"], inline=True)
            embed.set_thumbnail(url=user.avatar.url if user.avatar else discord.Embed.Empty)
            await ctx.send(embed=embed)
            return

        self.banned_users[str(user.id)] = {
            "username": user.name,
            "reason": reason,
            "banned_by": ctx.author.name
        }
        self.save_banned_users()

        embed = discord.Embed(
            title="Commands Global Ban - Success",
            description=f"{user.mention} has been banned from using bot commands.",
            color=discord.Color.green()
        )
        embed.add_field(name="User", value=user.name, inline=True)
        embed.add_field(name="User ID", value=user.id, inline=True)
        embed.add_field(name="Reason", value=reason, inline=True)
        embed.add_field(name="Command banned in", value=self.get_guilds_list(), inline=False)
        embed.add_field(name="Issued by", value=ctx.author.name, inline=True)
        embed.set_thumbnail(url=user.avatar.url if user.avatar else discord.Embed.Empty)
        await ctx.send(embed=embed)

    @cmd.command(name="ungban")
    @commands.has_permissions(administrator=True)
    async def ungban(self, ctx, user: discord.User):
        """Unban a user from using bot commands."""
        if str(user.id) not in self.banned_users:
            embed = discord.Embed(
                title="Commands Global Unban - Failed",
                description=f"{user.mention} is not banned from using bot commands.",
                color=discord.Color.red()
            )
            embed.add_field(name="User", value=user.name, inline=True)
            embed.add_field(name="User ID", value=user.id, inline=True)
            embed.add_field(name="Command banned in", value=self.get_guilds_list(), inline=False)
            embed.add_field(name="Issued by", value=ctx.author.name, inline=True)
            embed.set_thumbnail(url=user.avatar.url if user.avatar else discord.Embed.Empty)
            await ctx.send(embed=embed)
            return

        del self.banned_users[str(user.id)]
        self.save_banned_users()

        embed = discord.Embed(
            title="Commands Global Unban - Success",
            description=f"{user.mention} has been unbanned from using bot commands.",
            color=discord.Color.green()
        )
        embed.add_field(name="User", value=user.name, inline=True)
        embed.add_field(name="User ID", value=user.id, inline=True)
        embed.add_field(name="Command banned in", value=self.get_guilds_list(), inline=False)
        embed.add_field(name="Issued by", value=ctx.author.name, inline=True)
        embed.set_thumbnail(url=user.avatar.url if user.avatar else discord.Embed.Empty)
        await ctx.send(embed=embed)

    @cmd.command(name="list")
    @commands.has_permissions(administrator=True)
    async def list_banned(self, ctx):
        """List all users banned from using bot commands."""
        if not self.banned_users:
            embed = discord.Embed(
                title="Banned Users List",
                description="No users are currently banned from using bot commands.",
                color=discord.Color.blue()
            )
            await ctx.send(embed=embed)
            return

        embed = discord.Embed(
            title="Users Banned from Using Bot Commands",
            description="Here is the list of all the users who got banned from using the bot commands",
            color=discord.Color.blue()
        )
        for user_id, data in self.banned_users.items():
            embed.add_field(
                name=f"{data['username']} : {user_id}",
                value=f"Reason: {data['reason']} | Admin: {data['banned_by']}",
                inline=False
            )

        await ctx.send(embed=embed)

    @cmd.command(name="status")
    @commands.has_permissions(administrator=True)
    async def status(self, ctx, user: discord.User):
        """Check the command ban status of a user."""
        user_id = str(user.id)
        is_banned = user_id in self.banned_users

        embed = discord.Embed(
            title="User Status (Commands Bans)",
            color=discord.Color.blue()
        )
        embed.add_field(name="Username", value=user.name, inline=False)
        embed.add_field(name="User ID", value=user.id, inline=False)
        embed.add_field(name="Banned?", value="Yes" if is_banned else "No", inline=False)
        embed.add_field(
            name="Reason",
            value=self.banned_users[user_id]["reason"] if is_banned else "N/A",
            inline=False
        )
        embed.add_field(
            name="Moderator",
            value=self.banned_users[user_id]["banned_by"] if is_banned else "N/A",
            inline=False
        )
        embed.set_thumbnail(url=user.avatar.url if user.avatar else discord.Embed.Empty)
        await ctx.send(embed=embed)

    async def cog_command_error(self, ctx, error):
        """Handle errors for the commands in this cog."""
        embed = discord.Embed(title="Command Error", color=discord.Color.red())
        if isinstance(error, commands.MissingPermissions):
            embed.description = "You need administrator permissions to use this command."
        elif isinstance(error, commands.MissingRequiredArgument):
            embed.description = "Missing required arguments. Usage: ,cmd gban <user> <reason>, ,cmd ungban <user>, or ,cmd status <user>"
        else:
            embed.description = f"An error occurred: {str(error)}"
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(CommandsBan(bot))
