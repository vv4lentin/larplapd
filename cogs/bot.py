import discord
from discord.ext import commands
from discord.ui import Button, View

class Bot(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.owner_id = 1038522974988411000
        self.alert_channel_id = 1325937069377196042

    async def check_owner(self, ctx):
        if ctx.author.id != self.owner_id:
            alert_channel = self.bot.get_channel(self.alert_channel_id)
            if alert_channel:
                embed = discord.Embed(
                    title="⛔️ Restricted Commands Executed ⛔️",
                    description=(
                        f"An only owner command has been executed.\n"
                        f"**Command**: {ctx.command.name}\n"
                        f"[Jump to Message]({ctx.message.jump_url})"
                    ),
                    color=discord.Color.red()
                )
                embed.set_footer(text=f"User: {ctx.author} ({ctx.author.id})")
                await alert_channel.send(embed=embed)
            return False
        return True

    @commands.command()
    async def botpanel(self, ctx):
        if not await self.check_owner(ctx):
            return

        embed = discord.Embed(
            title="Bot Panel",
            description="Hello, please select an action.",
            color=discord.Color.blue()
        )

        view = View()

        # Button 1: Set DND
        button_dnd = Button(label="Set DND", style=discord.ButtonStyle.red)
        async def dnd_callback(interaction):
            if interaction.user.id != self.owner_id:
                return
            await self.bot.change_presence(status=discord.Status.dnd)
            await interaction.response.send_message("Status set to DND.", ephemeral=True)
        button_dnd.callback = dnd_callback

        # Button 2: Set Idle
        button_idle = Button(label="Set Idle", style=discord.ButtonStyle.yellow)
        async def idle_callback(interaction):
            if interaction.user.id != self.owner_id:
                return
            await self.bot.change_presence(status=discord.Status.idle)
            await interaction.response.send_message("Status set to Idle.", ephemeral=True)
        button_idle.callback = idle_callback

        # Button 3: Set Inactive
        button_inactive = Button(label="Set Inactive", style=discord.ButtonStyle.grey)
        async def inactive_callback(interaction):
            if interaction.user.id != self.owner_id:
                return
            await self.bot.change_presence(status=discord.Status.invisible)
            await interaction.response.send_message("Status set to Inactive.", ephemeral=True)
        button_inactive.callback = inactive_callback

        # Button 4: Set Online
        button_online = Button(label="Set Online", style=discord.ButtonStyle.green)
        async def online_callback(interaction):
            if interaction.user.id != self.owner_id:
                return
            await self.bot.change_presence(status=discord.Status.online)
            await interaction.response.send_message("Status set to Online.", ephemeral=True)
        button_online.callback = online_callback

        # Button 5: Set Activity
        button_activity = Button(label="Set Activity", style=discord.ButtonStyle.blurple)
        async def activity_callback(interaction):
            if interaction.user.id != self.owner_id:
                return
            await self.bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="Los Angeles Police Department"))
            await interaction.response.send_message("Activity set to 'Watching Los Angeles Police Department'.", ephemeral=True)
        button_activity.callback = activity_callback

        # Button 6: Shutdown
        button_shutdown = Button(label="Shutdown", style=discord.ButtonStyle.danger)
        async def shutdown_callback(interaction):
            if interaction.user.id != self.owner_id:
                return
            await interaction.response.send_message("Shutting down...", ephemeral=True)
            await self.bot.close()
        button_shutdown.callback = shutdown_callback

        # Add buttons to view
        view.add_item(button_dnd)
        view.add_item(button_idle)
        view.add_item(button_inactive)
        view.add_item(button_online)
        view.add_item(button_activity)
        view.add_item(button_shutdown)

        await ctx.send(embed=embed, view=view)

    @commands.command()
    async def purge(self, ctx, amount: int):
        if not await self.check_owner(ctx):
            return

        if amount < 1:
            await ctx.send("Please specify a number greater than 0.", delete_after=5)
            return

        # Check if bot has manage_messages permission
        if not ctx.channel.permissions_for(ctx.guild.me).manage_messages:
            await ctx.send("I don't have permission to manage messages in this channel.", delete_after=5)
            return

        await ctx.channel.purge(limit=amount + 1)  # +1 to include the command message
        await ctx.send(f"Purged {amount} message(s).", delete_after=5)

async def setup(bot):
    await bot.add_cog(Bot(bot))
