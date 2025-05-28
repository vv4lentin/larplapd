import discord
from discord.ext import commands
from discord import app_commands, ButtonStyle, Interaction
from datetime import datetime

# Role and Channel IDs
PERMS_ROLE_ID = 1376656549623234611  # Role ID for permission to use !warrant
PING_ROLE_ID = 1292541838904791040   # Role ID to ping when warrant is logged
LOG_CHANNEL_ID = 1325937069377196042  # Channel ID for unauthorized access logs
ALERT_ROLE_ID = 1337050305153470574  # Role to ping for unauthorized access

class WarrantModal(discord.ui.Modal, title="Log a Warrant"):
    def __init__(self):
        super().__init__()
        self.suspect = discord.ui.TextInput(
            label="Suspect",
            placeholder="Enter suspect(s) name",
            required=True
        )
        self.description = discord.ui.TextInput(
            label="Description",
            placeholder="Enter suspect description",
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
            placeholder="Enter head officer name and callsign",
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

class WarrantButton(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Log a Warrant", style=ButtonStyle.red)
    async def warrant_button(self, interaction: Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(WarrantModal())

class LAPD(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    @commands.command(name="warrant")
    async def warrant(self, ctx: commands.Context):
        if PERMS_ROLE_ID not in [role.id for role in ctx.author.roles]:
            # Send unauthorized message to channel (not ephemeral)
            await ctx.send("Unauthorized access detected ⚠️ ! An alert has been sent to the bot tamer.")
            # Send embed to log channel
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
            return
        view = WarrantButton()
        await ctx.send("Click the button to log a warrant (restricted access):", view=view)

async def setup(bot):
    await bot.add_cog(LAPD(bot))
