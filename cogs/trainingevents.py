import discord
from discord import Embed, Colour, ButtonStyle, Interaction, Member, Permissions
from discord.ui import Button, View, Modal, TextInput
from discord.ext import commands

class CancelButton(View):
    def __init__(self, host: str, original_message_id: int, event_type: str):
        super().__init__(timeout=None)
        self.host = host
        self.original_message_id = original_message_id
        self.event_type = event_type

    @discord.ui.button(label="Cancel", style=ButtonStyle.red)
    async def cancel_button(self, interaction: Interaction, button: Button):
        if interaction.user.display_name != self.host:
            await interaction.response.send_message(f"Only the host can cancel this {self.event_type.lower()}!", ephemeral=True)
            return
        
        await interaction.response.send_message(content=f"{self.event_type} cancelled.", reply_to=self.original_message_id)
        button.disabled = True
        await interaction.message.edit(view=self)

# Modal for Training Announcement
class TrainingModal(Modal, title="Training Announcement"):
    def __init__(self):
        super().__init__()
        self.when = TextInput(label="When", required=True)
        self.location = TextInput(label="Location", required=True)
        self.servercode = TextInput(label="Server Code", required=True)
        self.cohost = TextInput(label="Co-Host / Helpers (Optional)", required=False)
        self.notes = TextInput(label="Notes (Optional)", required=False, style=discord.TextStyle.paragraph)
        self.add_item(self.when)
        self.add_item(self.location)
        self.add_item(self.servercode)
        self.add_item(self.cohost)
        self.add_item(self.notes)

    async def on_submit(self, interaction: Interaction):
        channel = interaction.client.get_channel(1329908997381296220)
        if not channel:
            await interaction.response.send_message("Error: Target channel not found.", ephemeral=True)
            return

        embed = Embed(
            title="LAPD • Training Announcement",
            description="React if attending ✅",
            colour=Colour.blue()
        )
        embed.add_field(name="Host", value=interaction.user.display_name, inline=False)
        embed.add_field(name="Co-Host / Helpers", value=self.cohost.value if self.cohost.value else "N/A", inline=False)
        embed.add_field(name="When", value=self.when.value, inline=False)
        embed.add_field(name="Location", value=self.location.value, inline=False)
        embed.add_field(name="Server code", value=self.servercode.value, inline=False)
        embed.add_field(name="Notes", value=self.notes.value if self.notes.value else "N/A", inline=False)
        embed.set_footer(text=f"Sent by {interaction.user.display_name}")

        view = CancelButton(host=interaction.user.display_name, original_message_id=None, event_type="Training")
        await channel.send(content="<@&1306380788056723578> <@&1306380827143180340>")
        message = await channel.send(embed=embed, view=view)
        view.original_message_id = message.id
        await message.edit(view=view)
        await message.add_reaction("✅")
        await interaction.response.send_message("Training announcement sent successfully!", ephemeral=True)

# Modal for Orientation Announcement
class OrientationModal(Modal, title="Orientation Announcement"):
    def __init__(self):
        super().__init__()
        self.when = TextInput(label="When", required=True)
        self.location = TextInput(label="Location", required=True)
        self.servercode = TextInput(label="Server Code", required=True)
        self.cohost = TextInput(label="Co-Host / Helpers (Optional)", required=False)
        self.notes = TextInput(label="Notes (Optional)", required=False, style=discord.TextStyle.paragraph)
        self.add_item(self.when)
        self.add_item(self.location)
        self.add_item(self.servercode)
        self.add_item(self.cohost)
        self.add_item(self.notes)

    async def on_submit(self, interaction: Interaction):
        channel = interaction.client.get_channel(1329908997381296220)
        if not channel:
            await interaction.response.send_message("Error: Target channel not found.", ephemeral=True)
            return

        embed = Embed(
            title="LAPD • Orientation Announcement",
            description="React if attending ✅",
            colour=Colour.blue()
        )
        embed.add_field(name="Host", value=interaction.user.display_name, inline=False)
        embed.add_field(name="Co-Host / Helpers", value=self.cohost.value if self.cohost.value else "N/A", inline=False)
        embed.add_field(name="When", value=self.when.value, inline=False)
        embed.add_field(name="Location", value=self.location.value, inline=False)
        embed.add_field(name="Server code", value=self.servercode.value, inline=False)
        embed.add_field(name="Notes", value=self.notes.value if self.notes.value else "N/A", inline=False)
        embed.set_footer(text=f"Sent by {interaction.user.display_name}")

        view = CancelButton(host=interaction.user.display_name, original_message_id=None, event_type="Orientation")
        await channel.send(content="<@&1306380788056723578> <@&1306380858437144576>")
        message = await channel.send(embed=embed, view=view)
        view.original_message_id = message.id
        await message.edit(view=view)
        await message.add_reaction("✅")
        await interaction.response.send_message("Orientation announcement sent successfully!", ephemeral=True)

# Modal for Log Orientation Result
class LogOrientationModal(Modal, title="Log Orientation Result"):
    def __init__(self, trainee: Member):
        super().__init__()
        self.trainee = trainee
        self.result = TextInput(label="Result", required=True)
        self.comments = TextInput(label="Comments", required=True, style=discord.TextStyle.paragraph)
        self.cohost = TextInput(label="Co-Host / Helpers (Optional)", required=False)
        self.add_item(self.result)
        self.add_item(self.comments)
        self.add_item(self.cohost)

    async def on_submit(self, interaction: Interaction):
        channel = interaction.client.get_channel(1328036335826763939)
        if not channel:
            await interaction.response.send_message("Error: Target channel not found.", ephemeral=True)
            return

        role = interaction.guild.get_role(1306380827143180340)
        if not role:
            await interaction.response.send_message("Error: Target role not found.", ephemeral=True)
            return

        try:
            await self.trainee.add_roles(role)
        except Exception as e:
            await interaction.response.send_message(f"Error: Failed to add role to trainee. {str(e)}", ephemeral=True)
            return

        embed = Embed(
            title="Orientation • Result",
            colour=Colour.blue()
        )
        embed.add_field(name="Host", value=interaction.user.display_name, inline=False)
        embed.add_field(name="Co-Hosts", value=self.cohost.value if self.cohost.value else "N/A", inline=False)
        embed.add_field(name="Trainee", value=self.trainee.mention, inline=False)
        embed.add_field(name="Result", value=self.result.value, inline=False)
        embed.add_field(name="Comments", value=self.comments.value, inline=False)
        embed.set_footer(text=f"Issued by {interaction.user.display_name}")

        await channel.send(content=self.trainee.mention, embed=embed)
        await interaction.response.send_message("Orientation result logged successfully!", ephemeral=True)

# Modal for Log Training Result
class LogTrainingModal(Modal, title="Log Training Result"):
    def __init__(self, trainee: Member):
        super().__init__()
        self.trainee = trainee
        self.result = TextInput(label="Result", required=True)
        self.comments = TextInput(label="Comments", required=True, style=discord.TextStyle.paragraph)
        self.cohost = TextInput(label="Co-Host / Helpers (Optional)", required=False)
        self.add_item(self.result)
        self.add_item(self.comments)
        self.add_item(self.cohost)

    async def on_submit(self, interaction: Interaction):
        channel = interaction.client.get_channel(1329939121086529566)
        if not channel:
            await interaction.response.send_message("Error: Target channel not found.", ephemeral=True)
            return

        role = interaction.guild.get_role(1306380805752361020)
        if not role:
            await interaction.response.send_message("Error: Target role not found.", ephemeral=True)
            return

        try:
            await self.trainee.add_roles(role)
        except Exception as e:
            await interaction.response.send_message(f"Error: Failed to add role to trainee. {str(e)}", ephemeral=True)
            return

        embed = Embed(
            title="Training • Result",
            description=f"{self.trainee.mention} Please take your final exam.",
            colour=Colour.blue()
        )
        embed.add_field(name="Host", value=interaction.user.display_name, inline=False)
        embed.add_field(name="Co-Hosts", value=self.cohost.value if self.cohost.value else "N/A", inline=False)
        embed.add_field(name="Trainee", value=self.trainee.mention, inline=False)
        embed.add_field(name="Result", value=self.result.value, inline=False)
        embed.add_field(name="Comments", value=self.comments.value, inline=False)
        embed.set_footer(text=f"Issued by {interaction.user.display_name}")

        await channel.send(content=self.trainee.mention, embed=embed)
        await interaction.response.send_message("Training result logged successfully!", ephemeral=True)

# Modal for Log Mass Shift Result
class LogMassShiftModal(Modal, title="Log Mass Shift Result"):
    def __init__(self):
        super().__init__()
        self.started = TextInput(label="Started at", required=True)
        self.ended = TextInput(label="Ended at", required=True)
        self.attendedusers = TextInput(label="Attended Users", required=True)
        self.promotedusers = TextInput(label="Promoted Users", required=True)
        self.cohost = TextInput(label="Co-Host / Helpers (Optional)", required=False)
        self.add_item(self.started)
        self.add_item(self.ended)
        self.add_item(self.attendedusers)
        self.add_item(self.promotedusers)
        self.add_item(self.cohost)

    async def on_submit(self, interaction: Interaction):
        channel = interaction.client.get_channel(1328036189973909655)
        if not channel:
            await interaction.response.send_message("Error: Target channel not found.", ephemeral=True)
            return

        embed = Embed(
            title="LAPD • Mass Shift",
            colour=Colour.blue()
        )
        embed.add_field(name="Host", value=interaction.user.display_name, inline=False)
        embed.add_field(name="Co-Hosts", value=self.cohost.value if self.cohost.value else "N/A", inline=False)
        embed.add_field(name="Started at", value=self.started.value, inline=False)
        embed.add_field(name="Ended at", value=self.ended.value, inline=False)
        embed.add_field(name="Attended users", value=self.attendedusers.value, inline=False)
        embed.add_field(name="Promoted users", value=self.promotedusers.value, inline=False)
        embed.set_footer(text=f"Issued by {interaction.user.display_name}")

        await channel.send(embed=embed)
        await interaction.response.send_message("Mass shift result logged successfully!", ephemeral=True)

# Modal for Log SWAT Deployment Result
class LogSWATDeploymentModal(Modal, title="Log SWAT Deployment Result"):
    def __init__(self):
        super().__init__()
        self.started = TextInput(label="Started at", required=True)
        self.ended = TextInput(label="Ended at", required=True)
        self.attendedusers = TextInput(label="Attended Users", required=True)
        self.promotedusers = TextInput(label="Promoted Users", required=True)
        self.cohost = TextInput(label="Co-Host / Helpers (Optional)", required=False)
        self.add_item(self.started)
        self.add_item(self.ended)
        self.add_item(self.attendedusers)
        self.add_item(self.promotedusers)
        self.add_item(self.cohost)

    async def on_submit(self, interaction: Interaction):
        channel = interaction.client.get_channel(1348476059036815463)
        if not channel:
            await interaction.response.send_message("Error: Target channel not found.", ephemeral=True)
            return

        embed = Embed(
            title="LAPD • SWAT Deployment",
            colour=Colour.blue()
        )
        embed.add_field(name="Host", value=interaction.user.display_name, inline=False)
        embed.add_field(name="Co-Hosts", value=self.cohost.value if self.cohost.value else "N/A", inline=False)
        embed.add_field(name="Started at", value=self.started.value, inline=False)
        embed.add_field(name="Ended at", value=self.ended.value, inline=False)
        embed.add_field(name="Attended users", value=self.attendedusers.value, inline=False)
        embed.add_field(name="Promoted users", value=self.promotedusers.value, inline=False)
        embed.set_footer(text=f"Issued by {interaction.user.display_name}")

        await channel.send(embed=embed)
        await interaction.response.send_message("SWAT deployment result logged successfully!", ephemeral=True)

# View for Event Announcements
class EventsView(View):
    def __init__(self):
        super().__init__(timeout=60)

    @discord.ui.button(label="Announce Training", style=ButtonStyle.green)
    async def training_button(self, interaction: Interaction, button: Button):
        try:
            await interaction.response.send_modal(TrainingModal())
        except Exception as e:
            await interaction.response.send_message(f"Error launching Training modal: {str(e)}", ephemeral=True)

    @discord.ui.button(label="Announce Orientation", style=ButtonStyle.green)
    async def orientation_button(self, interaction: Interaction, button: Button):
        try:
            await interaction.response.send_modal(OrientationModal())
        except Exception as e:
            await interaction.response.send_message(f"Error launching Orientation modal: {str(e)}", ephemeral=True)

    @discord.ui.button(label="Announce Mass Shift", style=ButtonStyle.green)
    async def mass_shift_button(self, interaction: Interaction, button: Button):
        try:
            channel = interaction.client.get_channel(1292541172807635066)
            if not channel:
                await interaction.response.send_message("Error: Target channel not found.", ephemeral=True)
                return
            message = await channel.send(
                content=f"||<@&1292541838904791040>||\n{interaction.user.display_name} is hosting a **MASS SHIFT**.\n3+ votes required to start\nReact if attending ✅"
            )
            await message.add_reaction("✅")
            await interaction.response.send_message("Mass shift announcement sent successfully!", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"Error sending Mass Shift announcement: {str(e)}", ephemeral=True)

    @discord.ui.button(label="Announce SWAT Deployment", style=ButtonStyle.green)
    async def swat_deployment_button(self, interaction: Interaction, button: Button):
        try:
            channel = interaction.client.get_channel(1348476059036815463)
            if not channel:
                await interaction.response.send_message("Error: Target channel not found.", ephemeral=True)
                return
            message = await channel.send(
                content=f"||<@&1306381401830064201>||\n{interaction.user.display_name} is hosting a **SWAT DEPLOYMENT**.\n3+ votes required to start\nReact if attending ✅"
            )
            await message.add_reaction("✅")
            await interaction.response.send_message("SWAT deployment announcement sent successfully!", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"Error sending SWAT Deployment announcement: {str(e)}", ephemeral=True)

# View for Result Logging
class ResultView(View):
    def __init__(self, trainee: Member = None):
        super().__init__(timeout=60)
        self.trainee = trainee
        if not trainee:
            self.log_training_button.disabled = True
            self.log_orientation_button.disabled = True

    @discord.ui.button(label="Log Training Result", style=ButtonStyle.blurple)
    async def log_training_button(self, interaction: Interaction, button: Button):
        try:
            await interaction.response.send_modal(LogTrainingModal(self.trainee))
        except Exception as e:
            await interaction.response.send_message(f"Error launching Training Result modal: {str(e)}", ephemeral=True)

    @discord.ui.button(label="Log Orientation Result", style=ButtonStyle.blurple)
    async def log_orientation_button(self, interaction: Interaction, button: Button):
        try:
            await interaction.response.send_modal(LogOrientationModal(self.trainee))
        except Exception as e:
            await interaction.response.send_message(f"Error launching Orientation Result modal: {str(e)}", ephemeral=True)

    @discord.ui.button(label="Log Mass Shift Result", style=ButtonStyle.blurple)
    async def log_mass_shift_button(self, interaction: Interaction, button: Button):
        try:
            await interaction.response.send_modal(LogMassShiftModal())
        except Exception as e:
            await interaction.response.send_message(f"Error launching Mass Shift Result modal: {str(e)}", ephemeral=True)

    @discord.ui.button(label="Log SWAT Deployment Result", style=ButtonStyle.blurple)
    async def log_swat_deployment_button(self, interaction: Interaction, button: Button):
        try:
            await interaction.response.send_modal(LogSWATDeploymentModal())
        except Exception as e:
            await interaction.response.send_message(f"Error launching SWAT Deployment Result modal: {str(e)}", ephemeral=True)

class TrainingEvents(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="events", description="Shows the event announcement panel.")
    async def events(self, ctx: commands.Context):
        view = EventsView()
        await ctx.send("Event Announcement Panel", view=view, delete_after=60)

    @commands.hybrid_command(name="result", description="Shows the result logging panel for a user or mass shift/SWAT deployment.")
    async def result(self, ctx: commands.Context, user: Member = None):
        view = ResultView(trainee=user)
        await ctx.send("Result Logging Panel" + (f" for {user.mention}" if user else ""), view=view, delete_after=60)

    @commands.hybrid_command(name="sync", description="Syncs slash commands for the specified guild.")
    @commands.has_permissions(administrator=True)
    async def sync(self, ctx: commands.Context):
        if str(ctx.guild.id) != "1292523481539543193":
            await ctx.send("Error: This command can only be used in the specified guild.", delete_after=10, ephemeral=True)
            return

        try:
            synced = await ctx.bot.tree.sync(guild=discord.Object(id=1292523481539543193))
            await ctx.send(f"Successfully synced {len(synced)} commands for the guild!", delete_after=10, ephemeral=True)
        except Exception as e:
            await ctx.send(f"Error: Failed to sync commands. {str(e)}", delete_after=10, ephemeral=True)

async def setup(bot):
    await bot.add_cog(TrainingEvents(bot))
