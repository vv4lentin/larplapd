import discord
from discord import app_commands, Embed, Colour, ButtonStyle, Interaction, Member, Permissions
from discord.ui import Button, View
from discord.ext import commands

class CancelButton(View):
    def __init__(self, host: str, original_message_id: int, event_type: str):
        super().__init__(timeout=None)  # Persistent view
        self.host = host
        self.original_message_id = original_message_id
        self.event_type = event_type  # To differentiate between Training and Orientation

    @discord.ui.button(label="Cancel", style=ButtonStyle.red)
    async def cancel_button(self, interaction: Interaction, button: Button):
        if interaction.user.display_name != self.host:
            await interaction.response.send_message(f"Only the host can cancel this {self.event_type.lower()}!", ephemeral=True)
            return
        
        # Reply to the original message
        await interaction.response.send_message(content=f"{self.event_type} cancelled.", reply_to=self.original_message_id)
        # Disable the button after use
        button.disabled = True
        await interaction.message.edit(view=self)

class TrainingEvents(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="sync", description="Syncs slash commands for the specified guild.")
    async def sync(self, ctx: commands.Context):
        # Check if the command is run in the correct guild
        if str(ctx.guild.id) != "1292523481539543193":
            await ctx.send("Error: This command can only be used in the specified guild.", delete_after=10)
            return

        try:
            # Sync commands for the specific guild
            synced = await self.bot.tree.sync(guild=discord.Object(id=1292523481539543193))
            await ctx.send(f"Successfully synced {len(synced)} commands for the guild!", delete_after=10)
        except Exception as e:
            await ctx.send(f"Error: Failed to sync commands. {str(e)}", delete_after=10)

    @app_commands.command(name="training", description="Announces a training in the specified channel.")
    @app_commands.describe(
        host="The host of the training.",
        cohost="The co-host or helpers of the training (optional).",
        when="When the training will take place.",
        location="The location of the training.",
        servercode="The server code for the training.",
        notes="Additional notes for the training (optional)."
    )
    async def training(self, interaction: discord.Interaction, host: str, when: str, location: str, servercode: str, cohost: str = None, notes: str = None):
        # Defer the response to avoid timeout
        await interaction.response.defer(ephemeral=True)

        # Define the target channel
        channel = self.bot.get_channel(1329908997381296220)
        if not channel:
            await interaction.followup.send("Error: Target channel not found.", ephemeral=True)
            return

        # Create the embed
        embed = Embed(
            title="LAPD • Training Announcement",
            description="React if attending ✅",
            colour=Colour.blue()
        )
        embed.add_field(name="Host", value=host, inline=False)
        embed.add_field(name="Co-Host / Helpers", value=cohost if cohost else "N/A", inline=False)
        embed.add_field(name="When", value=when, inline=False)
        embed.add_field(name="Location", value=location, inline=False)
        embed.add_field(name="Server code", value=servercode, inline=False)
        embed.add_field(name="Notes", value=notes if notes else "N/A", inline=False)
        embed.set_footer(text=f"Sent by {interaction.user.display_name}")

        # Create the view with the Cancel button
        view = CancelButton(host=host, original_message_id=None, event_type="Training")

        # Send the ping message
        await channel.send(content="<@&1306380788056723578> <@&1306380827143180340>")

        # Send the embed with the button
        message = await channel.send(
            embed=embed,
            view=view
        )

        # Update the view with the message ID for replying
        view.original_message_id = message.id
        await message.edit(view=view)

        # Add the ✅ reaction
        await message.add_reaction("✅")

        # Confirm command execution
        await interaction.followup.send("Training announcement sent successfully!", ephemeral=True)

    @app_commands.command(name="orientation", description="Announces an orientation in the specified channel.")
    @app_commands.describe(
        host="The host of the orientation.",
        cohost="The co-host or helpers of the orientation (optional).",
        when="When the orientation will take place.",
        location="The location of the orientation.",
        servercode="The server code for the orientation.",
        notes="Additional notes for the orientation (optional)."
    )
    async def orientation(self, interaction: discord.Interaction, host: str, when: str, location: str, servercode: str, cohost: str = None, notes: str = None):
        # Defer the response to avoid timeout
        await interaction.response.defer(ephemeral=True)

        # Define the target channel
        channel = self.bot.get_channel(1329908997381296220)
        if not channel:
            await interaction.followup.send("Error: Target channel not found.", ephemeral=True)
            return

        # Create the embed
        embed = Embed(
            title="LAPD • Orientation Announcement",
            description="React if attending ✅",
            colour=Colour.blue()
        )
        embed.add_field(name="Host", value=host, inline=False)
        embed.add_field(name="Co-Host / Helpers", value=cohost if cohost else "N/A", inline=False)
        embed.add_field(name="When", value=when, inline=False)
        embed.add_field(name="Location", value=location, inline=False)
        embed.add_field(name="Server code", value=servercode, inline=False)
        embed.add_field(name="Notes", value=notes if notes else "N/A", inline=False)
        embed.set_footer(text=f"Sent by {interaction.user.display_name}")

        # Create the view with the Cancel button
        view = CancelButton(host=host, original_message_id=None, event_type="Orientation")

        # Send the ping message
        await channel.send(content="<@&1306380788056723578> <@&1306380858437144576>")

        # Send the embed with the button
        message = await channel.send(
            embed=embed,
            view=view
        )

        # Update the view with the message ID for replying
        view.original_message_id = message.id
        await message.edit(view=view)

        # Add the ✅ reaction
        await message.add_reaction("✅")

        # Confirm command execution
        await interaction.followup.send("Orientation announcement sent successfully!", ephemeral=True)

    @app_commands.command(name="logorientation", description="Logs the result of an orientation in the specified channel.")
    @app_commands.describe(
        host="The host of the orientation.",
        cohost="The co-host or helpers of the orientation (optional).",
        trainee="The trainee who attended the orientation.",
        result="The result of the orientation.",
        comments="Additional comments about the orientation."
    )
    async def logorientation(self, interaction: discord.Interaction, host: str, cohost: str = None, trainee: Member = None, result: str = None, comments: str = None):
        # Defer the response to avoid timeout
        await interaction.response.defer(ephemeral=True)

        # Define the target channel
        channel = self.bot.get_channel(1328036335826763939)
        if not channel:
            await interaction.followup.send("Error: Target channel not found.", ephemeral=True)
            return

        # Check if trainee is provided and valid
        if not trainee:
            await interaction.followup.send("Error: A valid trainee must be provided.", ephemeral=True)
            return

        # Add the role to the trainee
        role = interaction.guild.get_role(1306380827143180340)
        if not role:
            await interaction.followup.send("Error: Target role not found.", ephemeral=True)
            return

        try:
            await trainee.add_roles(role)
        except Exception as e:
            await interaction.followup.send(f"Error: Failed to add role to trainee. {str(e)}", ephemeral=True)
            return

        # Create the embed
        embed = Embed(
            title="Orientation • Result",
            colour=Colour.blue()
        )
        embed.add_field(name="Host", value=host, inline=False)
        embed.add_field(name="Co-Hosts", value=cohost if cohost else "N/A", inline=False)
        embed.add_field(name="Trainee", value=trainee.mention, inline=False)
        embed.add_field(name="Result", value=result if result else "N/A", inline=False)
        embed.add_field(name="Comments", value=comments if comments else "N/A", inline=False)
        embed.set_footer(text=f"Issued by {interaction.user.display_name}")

        # Send the trainee ping and embed
        await channel.send(content=trainee.mention, embed=embed)

        # Confirm command execution
        await interaction.followup.send("Orientation result logged successfully!", ephemeral=True)

    @app_commands.command(name="logtraining", description="Logs the result of a training in the specified channel.")
    @app_commands.describe(
        host="The host of the training.",
        cohost="The co-host or helpers of the training (optional).",
        trainee="The trainee who attended the training.",
        result="The result of the training.",
        comments="Additional comments about the training."
    )
    async def logtraining(self, interaction: discord.Interaction, host: str, cohost: str = None, trainee: Member = None, result: str = None, comments: str = None):
        # Defer the response to avoid timeout
        await interaction.response.defer(ephemeral=True)

        # Define the target channel
        channel = self.bot.get_channel(1329939121086529566)
        if not channel:
            await interaction.followup.send("Error: Target channel not found.", ephemeral=True)
            return

        # Check if trainee is provided and valid
        if not trainee:
            await interaction.followup.send("Error: A valid trainee must be provided.", ephemeral=True)
            return

        # Add the role to the trainee
        role = interaction.guild.get_role(1306380805752361020)
        if not role:
            await interaction.followup.send("Error: Target role not found.", ephemeral=True)
            return

        try:
            await trainee.add_roles(role)
        except Exception as e:
            await interaction.followup.send(f"Error: Failed to add role to trainee. {str(e)}", ephemeral=True)
            return

        # Create the embed
        embed = Embed(
            title="Training • Result",
            description=f"{trainee.mention} Please take your final exam.",
            colour=Colour.blue()
        )
        embed.add_field(name="Host", value=host, inline=False)
        embed.add_field(name="Co-Hosts", value=cohost if cohost else "N/A", inline=False)
        embed.add_field(name="Trainee", value=trainee.mention, inline=False)
        embed.add_field(name="Result", value=result if result else "N/A", inline=False)
        embed.add_field(name="Comments", value=comments if comments else "N/A", inline=False)
        embed.set_footer(text=f"Issued by {interaction.user.display_name}")

        # Send the trainee ping and embed
        await channel.send(content=trainee.mention, embed=embed)

        # Confirm command execution
        await interaction.followup.send("Training result logged successfully!", ephemeral=True)

    @app_commands.command(name="massshift", description="Announces a mass shift in the specified channel.")
    @app_commands.describe(
        host="The host of the mass shift."
    )
    async def massshift(self, interaction: discord.Interaction, host: str):
        # Defer the response to avoid timeout
        await interaction.response.defer(ephemeral=True)

        # Define the target channel
        channel = self.bot.get_channel(1292541172807635066)
        if not channel:
            await interaction.followup.send("Error: Target channel not found.", ephemeral=True)
            return

        # Send the message
        message = await channel.send(
            content=f"||<@&1292541838904791040>||\n{host} is hosting a **MASS SHIFT**.\n3+ votes required to start\nReact if attending ✅"
        )

        # Add the ✅ reaction
        await message.add_reaction("✅")

        # Confirm command execution
        await interaction.followup.send("Mass shift announcement sent successfully!", ephemeral=True)

    @app_commands.command(name="logmassshift", description="Logs the result of a mass shift in the specified channel.")
    @app_commands.describe(
        host="The host of the mass shift.",
        cohost="The co-host or helpers of the mass shift (optional).",
        started="When the mass shift started.",
        ended="When the mass shift ended.",
        attendedusers="Users who attended the mass shift.",
        promotedusers="Users who were promoted during the mass shift."
    )
    async def logmassshift(self, interaction: discord.Interaction, host: str, cohost: str = None, started: str = None, ended: str = None, attendedusers: str = None, promotedusers: str = None):
        # Defer the response to avoid timeout
        await interaction.response.defer(ephemeral=True)

        # Define the target channel
        channel = self.bot.get_channel(1328036189973909655)
        if not channel:
            await interaction.followup.send("Error: Target channel not found.", ephemeral=True)
            return

        # Create the embed
        embed = Embed(
            title="LAPD • Mass Shift",
            colour=Colour.blue()
        )
        embed.add_field(name="Host", value=host, inline=False)
        embed.add_field(name="Co-Hosts", value=cohost if cohost else "N/A", inline=False)
        embed.add_field(name="Started at", value=started if started else "N/A", inline=False)
        embed.add_field(name="Ended at", value=ended if ended else "N/A", inline=False)
        embed.add_field(name="Attended users", value=attendedusers if attendedusers else "N/A", inline=False)
        embed.add_field(name="Promoted users", value=promotedusers if promotedusers else "N/A", inline=False)
        embed.set_footer(text=f"Issued by {interaction.user.display_name}")

        # Send the embed
        await channel.send(embed=embed)

        # Confirm command execution
        await interaction.followup.send("Mass shift result logged successfully!", ephemeral=True)

async def setup(bot):
    await bot.add_cog(TrainingEvents(bot))
