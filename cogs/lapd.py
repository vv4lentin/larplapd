import discord
from discord.ext import commands
from discord import app_commands, ButtonStyle, Interaction
from datetime import datetime

# Role IDs
PERMS_ROLE_ID = 1376656549623234611  # Role ID for permission to use !warrant
PING_ROLE_ID = 1292541838904791040   # Role ID to ping when warrant is logged

class ArrestModal(discord.ui.Modal, title="Log an Arrest"):
    def __init__(self):
        super().__init__()
        self.suspect = discord.ui.TextInput(
            label="Suspect",
            placeholder="Enter suspect's name",
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
            placeholder="Enter primary officer name and callsign",
            required=True
        )
        self.other_officers = discord.ui.TextInput(
            label="Secondary and Tertiary Officers",
            placeholder="Enter other officers' names ot enter N/A",
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

class WarrantModal(discord.ui.Modal, title="Log a Warrant"):
    def __init__(self):
        super().__init__()
        self.suspect = discord.ui.TextInput(
            label="Suspect",
            placeholder="Enter suspect's name",
            required=True
        )
        self.description = discord.ui.TextInput(
            label="Description",
            placeholder="Enter warrant description",
            required=True,
            style=discord.TextStyle.paragraph
        )
        self.crimes = discord.ui.TextInput(
            label="Crimes",
            placeholder="List the crimes",
            required=True
        )
        self.head_of_case = discord.ui.TextInput(
            label="Head of Case",
            placeholder="Enter head officer's name",
            required=True
        )
        self.case_number = discord.ui.TextInput(
            label="Case Number",
            placeholder="Enter case number",
            required=True
        )
        self.add_item(self.suspect)
        self.add_item(self.description)
        self.add_item(self.crimes)
        self.add_item(self.head_of_case)
        self.add_item(self.case_number)

    async def on_submit(self, interaction: Interaction):
        embed = discord.Embed(
            title="🚨 New Warrant 🚨",
            description="A new warrant has just been issued.",
            color=discord.Color.red(),
            timestamp=datetime.now()
        )
        embed.add_field(name="Suspect", value=self.suspect.value, inline=False)
        embed.add_field(name="Description", value=self.description.value, inline=False)
        embed.add_field(name="Crimes", value=self.crimes.value, inline=False)
        embed.add_field(name="Head of Case", value=self.head_of_case.value, inline=False)
        embed.add_field(name="Case Number", value=self.case_number.value, inline=False)
        ping_message = f"<@&{PING_ROLE_ID}>"
        await interaction.response.send_message(content=ping_message, embed=embed)

class ArrestButton(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Log an Arrest", style=ButtonStyle.green)
    async def arrest_button(self, interaction: Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(ArrestModal())

class WarrantButton(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Log a Warrant", style=ButtonStyle.red)
    async def warrant_button(self, interaction: Interaction, button: discord.ui.Button):
        if PERMS_ROLE_ID not in [role.id for role in interaction.user.roles]:
            await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
            return
        await interaction.response.send_modal(WarrantModal())

class LAPD(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="arrest")
    async def arrest(self, ctx: commands.Context):
        view = ArrestButton()
        await ctx.send("Click the button to log an arrest:", view=view)

    @commands.command(name="warrant")
    async def warrant(self, ctx: commands.Context):
        view = WarrantButton()
        await ctx.send("Click the button to log a warrant:", view=view)

async def setup(bot):
    await bot.add_cog(LAPD(bot))
