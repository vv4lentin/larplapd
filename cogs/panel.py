import discord
from discord.ext import commands
from discord.ui import Button, View, Modal, TextInput
from discord import Interaction, TextStyle
from datetime import datetime

# Arrest Modal (as provided)
class ArrestModal(discord.ui.Modal, title="Log an Arrest"):
    def __init__(self):
        super().__init__()
        self.suspect = discord.ui.TextInput(
            label="Suspect",
            placeholder="Enter suspect(s) name",
            required=True
        )
        self.charges = discord.ui.TextInput(
            label="Charges",
            placeholder="List the charges",
            required=True,
            style=discord.TextStyle.paragraph
        )
        self.primary_officer = discord.ui.TextInput(
            label="Primary Officer",
            placeholder="Enter primary officer name",
            required=True
        )
        self.other_officers = discord.ui.TextInput(
            label="Secondary and Tertiary Officers",
            placeholder="Enter other officers names and their callsign or N/A",
            required=False
        )
        self.notes = discord.ui.TextInput(
            label="Notes",
            placeholder="Additional notes (optional)",
            required=False,
            style=discord.TextStyle.paragraph
        )
        self.add_item(self.suspect)
        self.add_item(self.charges)
        self.add_item(self.primary_officer)
        self.add_item(self.other_officers)
        self.add_item(self.notes)

    async def on_submit(self, interaction: Interaction):
        embed = discord.Embed(
            title="New Arrest Log",
            description="Please send the mugshot!",
            color=discord.Color.green(),
            timestamp=datetime.now()
        )
        embed.add_field(name="Suspect", value=self.suspect.value, inline=False)
        embed.add_field(name="Crimes", value=self.charges.value, inline=False)
        embed.add_field(name="Primary Officer", value=self.primary_officer.value, inline=False)
        embed.add_field(name="Secondary and Tertiary Officers", value=self.other_officers.value or "None", inline=False)
        embed.add_field(name="Notes", value=self.notes.value or "None", inline=False)
        await interaction.response.send_message(embed=embed)

# Panel Cog
class Panel(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Define the punishment roles
        self.punishment_roles = [
            1306382455044964415,  # Punishment Role 1
            1306382453283225650,  # Punishment Role 2
            1306382451228016660,  # Punishment Role 3
            1306382449378594867,  # Punishment Role 4
            1324540074834133033,  # Punishment Role 5
            1324540189594353787   # Punishment Role 6
        ]

    @commands.command(name="panel")
    async def panel(self, ctx):
        # Create the embed for the panel
        embed = discord.Embed(
            title="Welcome to Your Panel",
            description="Below you can see buttons for the following options.",
            color=discord.Color.blue()
        )
        embed.add_field(
            name="📝 Log Arrest",
            value="Use this to Log an Arrest.",
            inline=False
        )
        embed.add_field(
            name="👮 View Punishments",
            value="Use this to view your active Punishments.",
            inline=False
        )
        embed.set_thumbnail(url="https://upload.wikimedia.org/wikipedia/commons/thumb/5/5b/Los_Angeles_Police_Department_seal.svg/512px-Los_Angeles_Police_Department_seal.svg.png")
        embed.set_image(url="https://cdn.discordapp.com/attachments/1369422640003153961/1377358249044742174/Los_Angeles_Police_Department_1_1.png?ex=6838ac54&is=68375ad4&hm=e2dde275075c243188d3f18f71a984b486672877fff44ded4ae4baff3ca821fd&")

        # Create the buttons
        view = View(timeout=None)  # Persistent view

        # Log Arrest Button
        log_arrest_button = Button(label="Log Arrest", style=discord.ButtonStyle.primary, custom_id="log_arrest")
        async def log_arrest_callback(interaction: discord.Interaction):
            # Show the arrest modal when the button is clicked
            modal = ArrestModal()
            await interaction.response.send_modal(modal)
        log_arrest_button.callback = log_arrest_callback

        # View Punishments Button
        view_punishments_button = Button(label="View Punishments", style=discord.ButtonStyle.secondary, custom_id="view_punishments")
        async def view_punishments_callback(interaction: discord.Interaction):
            # Check user's roles against punishment roles
            user = interaction.user
            user_roles = [role.id for role in user.roles]
            active_punishments = [role for role in self.punishment_roles if role in user_roles]

            # Create an embed for the punishments
            embed = discord.Embed(
                title=f"Punishments for - {user.display_name} -",
                color=discord.Color.red(),
                timestamp=datetime.now()
            )
            embed.set_thumbnail(url="https://upload.wikimedia.org/wikipedia/commons/thumb/5/5b/Los_Angeles_Police_Department_seal.svg/512px-Los_Angeles_Police_Department_seal.svg.png")

            if active_punishments:
                # List the roles with pings
                punishment_list = "\n".join([f"<@&{role_id}>" for role_id in active_punishments])
                embed.description = punishment_list
            else:
                embed.description = "No active punishments."

            await interaction.response.send_message(embed=embed, ephemeral=True)
        view_punishments_button.callback = view_punishments_callback

        # Add buttons to the view
        view.add_item(log_arrest_button)
        view.add_item(view_punishments_button)

        # Send the embed with the buttons
        await ctx.send(embed=embed, view=view)

async def setup(bot):
    await bot.add_cog(Panel(bot))
