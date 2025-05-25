import discord
from discord import Embed, Colour, ButtonStyle, Interaction, Member, Permissions
from discord.ui import Button, View, Modal, TextInput
from discord.ext import commands

class CancelButton(View):
    def __init__(self, host: Member, original_message_id: int, event_type: str):
        super().__init__(timeout=None)
        self.host = host
        self.original_message_id = original_message_id
        self.event_type = event_type

    @discord.ui.button(label="Cancel", style=ButtonStyle.red)
    async def cancel_button(self, interaction: Interaction, button: Button):
        if interaction.user != self.host:
            await interaction.response.send_message(f"Only the host can cancel this {self.event_type.lower()}!", ephemeral=True)
            return
        
        await interaction.response.send_message(content=f"{self.event_type} cancelled.", reply_to=self.original_message_id)
        button.disabled = True
        await interaction.message.edit(view=self)

class TrainingModal(Modal, title="Training Announcement"):
    when = TextInput(label="When", placeholder="Enter date and time")
    location = TextInput(label="Location", placeholder="Enter location")
    servercode = TextInput(label="Server Code", placeholder="Enter server code")
    cohost = TextInput(label="Co-Host/Helpers (Optional)", required=False, placeholder="Enter co-host(s)")
    notes = TextInput(label="Notes (Optional)", required=False, placeholder="Enter additional notes")

    def __init__(self, bot, channel_id):
        super().__init__()
        self.bot = bot
        self.channel_id = channel_id

    async def on_submit(self, interaction: Interaction):
        channel = self.bot.get_channel(self.channel_id)
        if not channel:
            await interaction.response.send_message("Error: Target channel not found.", ephemeral=True)
            return

        embed = Embed(
            title="LAPD • Training Announcement",
            description="React if attending ✅",
            colour=Colour.blue()
        )
        embed.add_field(name="Host", value=interaction.user.display_name, inline=False)
        embed.add_field(name="Co-Host / Helpers", value=self.cohost.value or "N/A", inline=False)
        embed.add_field(name="When", value=self.when.value, inline=False)
        embed.add_field(name="Location", value=self.location.value, inline=False)
        embed.add_field(name="Server code", value=self.servercode.value, inline=False)
        embed.add_field(name="Notes", value=self.notes.value or "N/A", inline=False)
        embed.set_footer(text=f"Sent by {interaction.user.display_name}")

        view = CancelButton(host=interaction.user, original_message_id=None, event_type="Training")
        await channel.send(content="<@&1306380788056723578> <@&1306380827143180340>")
        message = await channel.send(embed=embed, view=view)
        view.original_message_id = message.id
        await message.edit(view=view)
        await message.add_reaction("✅")
        await interaction.response.send_message("Training announcement sent successfully!", ephemeral=True)

class OrientationModal(Modal, title="Orientation Announcement"):
    when = TextInput(label="When", placeholder="Enter date and time")
    location = TextInput(label="Location", placeholder="Enter location")
    servercode = TextInput(label="Server Code", placeholder="Enter server code")
    cohost = TextInput(label="Co-Host/Helpers (Optional)", required=False, placeholder="Enter co-host(s)")
    notes = TextInput(label="Notes (Optional)", required=False, placeholder="Enter additional notes")

    def __init__(self, bot, channel_id):
        super().__init__()
        self.bot = bot
        self.channel_id = channel_id

    async def on_submit(self, interaction: Interaction):
        channel = self.bot.get_channel(self.channel_id)
        if not channel:
            await interaction.response.send_message("Error: Target channel not found.", ephemeral=True)
            return

        embed = Embed(
            title="LAPD • Orientation Announcement",
            description="React if attending ✅",
            colour=Colour.blue()
        )
        embed.add_field(name="Host", value=interaction.user.display_name, inline=False)
        embed.add_field(name="Co-Host / Helpers", value=self.cohost.value or "N/A", inline=False)
        embed.add_field(name="When", value=self.when.value, inline=False)
        embed.add_field(name="Location", value=self.location.value, inline=False)
        embed.add_field(name="Server code", value=self.servercode.value, inline=False)
        embed.add_field(name="Notes", value=self.notes.value or "N/A", inline=False)
        embed.set_footer(text=f"Sent by {interaction.user.display_name}")

        view = CancelButton(host=interaction.user, original_message_id=None, event_type="Orientation")
        await channel.send(content="<@&1306380788056723578> <@&1306380858437144576>")
        message = await channel.send(embed=embed, view=view)
        view.original_message_id = message.id
        await message.edit(view=view)
        await message.add_reaction("✅")
        await interaction.response.send_message("Orientation announcement sent successfully!", ephemeral=True)

class LogOrientationModal(Modal, title="Log Orientation Result"):
    trainee = TextInput(label="Trainee (Mention)", placeholder="@username")
    result = TextInput(label="Result", placeholder="Enter result")
    comments = TextInput(label="Comments", placeholder="Enter comments")
    cohost = TextInput(label="Co-Hosts (Optional)", required=False, placeholder="Enter co-host(s)")

    def __init__(self, bot, channel_id):
        super().__init__()
        self.bot = bot
        self.channel_id = channel_id

    async def on_submit(self, interaction: Interaction):
        channel = self.bot.get_channel(self.channel_id)
        if not channel:
            await interaction.response.send_message("Error: Target channel not found.", ephemeral=True)
            return

        try:
            trainee_id = int(self.trainee.value.strip("<@!>").strip())
            trainee = interaction.guild.get_member(trainee_id)
            if not trainee:
                await interaction.response.send_message("Error: Invalid trainee provided.", ephemeral=True)
                return
        except ValueError:
            await interaction.response.send_message("Error: Please provide a valid trainee mention.", ephemeral=True)
            return

        role = interaction.guild.get_role(1306380827143180340)
        if not role:
            await interaction.response.send_message("Error: Target role not found.", ephemeral=True)
            return

        try:
            await trainee.add_roles(role)
        except Exception as e:
            await interaction.response.send_message(f"Error: Failed to add role to trainee. {str(e)}", ephemeral=True)
            return

        embed = Embed(
            title="Orientation • Result",
            colour=Colour.blue()
        )
        embed.add_field(name="Host", value=interaction.user.display_name, inline=False)
        embed.add_field(name="Co-Hosts", value=self.cohost.value or "N/A", inline=False)
        embed.add_field(name="Trainee", value=trainee.mention, inline=False)
        embed.add_field(name="Result", value=self.result.value or "N/A", inline=False)
        embed.add_field(name="Comments", value=self.comments.value or "N/A", inline=False)
        embed.set_footer(text=f"Issued by {interaction.user.display_name}")

        await channel.send(content=trainee.mention, embed=embed)
        await interaction.response.send_message("Orientation result logged successfully!", ephemeral=True)

class LogTrainingModal(Modal, title="Log Training Result"):
    trainee = TextInput(label="Trainee (Mention)", placeholder="@username")
    result = TextInput(label="Result", placeholder="Enter result")
    comments = TextInput(label="Comments", placeholder="Enter comments")
    cohost = TextInput(label="Co-Hosts (Optional)", required=False, placeholder="Enter co-host(s)")

    def __init__(self, bot, channel_id):
        super().__init__()
        self.bot = bot
        self.channel_id = channel_id

    async def on_submit(self, interaction: Interaction):
        channel = self.bot.get_channel(self.channel_id)
        if not channel:
            await interaction.response.send_message("Error: Target channel not found.", ephemeral=True)
            return

        try:
            trainee_id = int(self.trainee.value.strip("<@!>").strip())
            trainee = interaction.guild.get_member(trainee_id)
            if not trainee:
                await interaction.response.send_message("Error: Invalid trainee provided.", ephemeral=True)
                return
        except ValueError:
            await interaction.response.send_message("Error: Please provide a valid trainee mention.", ephemeral=True)
            return

        role = interaction.guild.get_role(1306380805752361020)
        if not role:
            await interaction.response.send_message("Error: Target role not found.", ephemeral=True)
            return

        try:
            await trainee.add_roles(role)
        except Exception as e:
            await interaction.response.send_message(f"Error: Failed to add role to trainee. {str(e)}", ephemeral=True)
            return

        embed = Embed(
            title="Training • Result",
            description=f"{trainee.mention} Please take your final exam.",
            colour=Colour.blue()
        )
        embed.add_field(name="Host", value=interaction.user.display_name, inline=False)
        embed.add_field(name="Co-Hosts", value=self.cohost.value or "N/A", inline=False)
        embed.add_field(name="Trainee", value=trainee.mention, inline=False)
        embed.add_field(name="Result", value=self.result.value or "N/A", inline=False)
        embed.add_field(name="Comments", value=self.comments.value or "N/A", inline=False)
        embed.set_footer(text=f"Issued by {interaction.user.display_name}")

        await channel.send(content=trainee.mention, embed=embed)
        await interaction.response.send_message("Training result logged successfully!", ephemeral=True)

class LogMassShiftModal(Modal, title="Log Mass Shift Result"):
    started = TextInput(label="Started At", placeholder="Enter start time")
    ended = TextInput(label="Ended At", placeholder="Enter end time")
    attendedusers = TextInput(label="Attended Users", placeholder="Enter attended users")
    promotedusers = TextInput(label="Promoted Users", placeholder="Enter promoted users")
    cohost = TextInput(label="Co-Hosts (Optional)", required=False, placeholder="Enter co-host(s)")

    def __init__(self, bot, channel_id):
        super().__init__()
        self.bot = bot
        self.channel_id = channel_id

    async def on_submit(self, interaction: Interaction):
        channel = self.bot.get_channel(self.channel_id)
        if not channel:
            await interaction.response.send_message("Error: Target channel not found.", ephemeral=True)
            return

        embed = Embed(
            title="LAPD • Mass Shift",
            colour=Colour.blue()
        )
        embed.add_field(name="Host", value=interaction.user.display_name, inline=False)
        embed.add_field(name="Co-Hosts", value=self.cohost.value or "N/A", inline=False)
        embed.add_field(name="Started at", value=self.started.value or "N/A", inline=False)
        embed.add_field(name="Ended at", value=self.ended.value or "N/A", inline=False)
        embed.add_field(name="Attended users", value=self.attendedusers.value or "N/A", inline=False)
        embed.add_field(name="Promoted users", value=self.promotedusers.value or "N/A", inline=False)
        embed.set_footer(text=f"Issued by {interaction.user.display_name}")

        await channel.send(embed=embed)
        await interaction.response.send_message("Mass shift result logged successfully!", ephemeral=True)

class TrainingEvents(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="training")
    async def training(self, ctx: commands.Context):
        modal = TrainingModal(self.bot, 1329908997381296220)
        await ctx.send_modal(modal)

    @commands.command(name="orientation")
    async def orientation(self, ctx: commands.Context):
        modal = OrientationModal(self.bot, 1329908997381296220)
        await ctx.send_modal(modal)

    @commands.command(name="logorientation")
    async def logorientation(self, ctx: commands.Context):
        modal = LogOrientationModal(self.bot, 1328036335826763939)
        await ctx.send_modal(modal)

    @commands.command(name="logtraining")
    async def logtraining(self, ctx: commands.Context):
        modal = LogTrainingModal(self.bot, 1329939121086529566)
        await ctx.send_modal(modal)

    @commands.command(name="massshift")
    async def massshift(self, ctx: commands.Context):
        channel = self.bot.get_channel(1292541172807635066)
        if not channel:
            await ctx.send("Error: Target channel not found.", delete_after=10)
            return

        message = await channel.send(
            content=f"||<@&1292541838904791040>||\n{ctx.author.display_name} is hosting a **MASS SHIFT**.\n3+ votes required to start\nReact if attending ✅"
        )
        await message.add_reaction("✅")
        await ctx.send("Mass shift announcement sent successfully!", delete_after=10)

    @commands.command(name="logmassshift")
    async def logmassshift(self, ctx: commands.Context):
        modal = LogMassShiftModal(self.bot, 1328036189973909655)
        await ctx.send_modal(modal)

    @commands.command(name="sync")
    @commands.has_permissions(administrator=True)
    async def sync(self, ctx: commands.Context):
        if str(ctx.guild.id) != "1292523481539543193":
            await ctx.send("Error: This command can only be used in the specified guild.", delete_after=10)
            return

        try:
            synced = await self.bot.tree.sync(guild=discord.Object(id=1292523481539543193))
            await ctx.send(f"Successfully synced {len(synced)} commands for the guild!", delete_after=10)
        except Exception as e:
            await ctx.send(f"Error: Failed to sync commands. {str(e)}", delete_after=10)

async def setup(bot):
    await bot.add_cog(TrainingEvents(bot))
