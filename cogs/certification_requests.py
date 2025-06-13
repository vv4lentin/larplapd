import discord
from discord import Embed, Colour, ButtonStyle, Interaction, Member
from discord.ui import Button, View, Select
from discord.ext import commands
import logging

# Set up logging for debugging
logging.basicConfig(level=logging.INFO)

# View for Certification Request Buttons (Accept/Deny)
class CertActionView(View):
    def __init__(self, user: Member, certification: str):
        super().__init__(timeout=None)  # Persistent view
        self.user = user
        self.certification = certification

    @discord.ui.button(label="Accept", style=ButtonStyle.green)
    async def accept_button(self, interaction: Interaction, button: Button):
        channel = interaction.client.get_channel(1304472122646859797)
        if not channel:
            logging.error("Target channel 1304472122646859797 not found")
            await interaction.response.send_message("Error: Target channel not found.", ephemeral=True)
            return

        embed = Embed(
            title="Certification Request Status",
            description=f"Certification Request for **{self.certification}** has been **accepted** by {interaction.user.display_name}.",
            colour=Colour.green()
        )
        embed.set_footer(text=f"Issued by {interaction.user.display_name}")

        try:
            await channel.send(content=self.user.mention, embed=embed)
            await interaction.response.send_message(f"Certification request for {self.certification} accepted!", ephemeral=True)
            logging.info(f"Certification {self.certification} accepted for {self.user} by {interaction.user}")
        except Exception as e:
            logging.error(f"Failed to send accept embed: {str(e)}")
            await interaction.response.send_message(f"Error sending accept message: {str(e)}", ephemeral=True)
        self.stop()
        await interaction.message.edit(view=None)  # Remove buttons after action

    @discord.ui.button(label="Deny", style=ButtonStyle.red)
    async def deny_button(self, interaction: Interaction, button: Button):
        channel = interaction.client.get_channel(1304472122646859797)
        if not channel:
            logging.error("Target channel 1304472122646859797 not found")
            await interaction.response.send_message("Error: Target channel not found.", ephemeral=True)
            return

        embed = Embed(
            title="Certification Request Status",
            description=f"Certification Request for **{self.certification}** has been **denied** by {interaction.user.display_name}.",
            colour=Colour.red()
        )
        embed.set_footer(text=f"Issued by {interaction.user.display_name}")

        try:
            await channel.send(content=self.user.mention, embed=embed)
            await interaction.response.send_message(f"Certification request for {self.certification} denied!", ephemeral=True)
            logging.info(f"Certification {self.certification} denied for {self.user} by {interaction.user}")
        except Exception as e:
            logging.error(f"Failed to send deny embed: {str(e)}")
            await interaction.response.send_message(f"Error sending deny message: {str(e)}", ephemeral=True)
        self.stop()
        await interaction.message.edit(view=None)  # Remove buttons after action

# View for Certification Request Dropdown
class CertRequestView(View):
    def __init__(self, user: Member, when: str):
        super().__init__(timeout=60)
        self.user = user
        self.when = when

    @discord.ui.select(
        placeholder="Select a Certification",
        options=[
            discord.SelectOption(label="Grappler", value="Grappler"),
            discord.SelectOption(label="Undercover", value="Undercover"),
            discord.SelectOption(label="Spike-Strip", value="Spike-Strip"),
            discord.SelectOption(label="Negotiator", value="Negotiator"),
            discord.SelectOption(label="Sniper", value="Sniper"),
            discord.SelectOption(label="G36C", value="G36C"),
            discord.SelectOption(label="Bearcat", value="Bearcat"),
        ]
    )
    async def select_callback(self, interaction: Interaction, select: Select):
        if interaction.user != self.user:
            await interaction.response.send_message("Only the user who initiated the request can select a certification!", ephemeral=True)
            logging.info(f"Unauthorized select attempt by {interaction.user} for {self.user}'s request")
            return

        channel = interaction.client.get_channel(1383124547900936242)
        if not channel:
            logging.error("Target channel 1383124547900936242 not found")
            await interaction.response.send_message("Error: Target channel not found.", ephemeral=True)
            return

        embed = Embed(
            title="Certification Request",
            colour=Colour.blue()
        )
        embed.add_field(name="User", value=f"{self.user.mention} ({self.user.id})", inline=False)
        embed.add_field(name="Certification", value=select.values[0], inline=False)
        embed.add_field(name="When", value=self.when, inline=False)
        embed.set_footer(text=f"Requested by {self.user.display_name}")

        view = CertActionView(user=self.user, certification=select.values[0])
        try:
            await channel.send(embed=embed, view=view)
            await interaction.response.send_message(f"Certification request for {select.values[0]} sent successfully!", ephemeral=True)
            logging.info(f"Certification request for {select.values[0]} sent by {self.user} to channel 1383124547900936242")
        except Exception as e:
            logging.error(f"Failed to send certification request embed: {str(e)}")
            await interaction.response.send_message(f"Error sending certification request: {str(e)}", ephemeral=True)
        self.stop()

class CertificationRequests(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        logging.info("CertificationRequests cog initialized")

    async def cog_load(self):
        logging.info("CertificationRequests cog loaded")
        # Sync commands for all guilds the bot is in (for debugging)
        try:
            for guild in self.bot.guilds:
                synced = await self.bot.tree.sync(guild=discord.Object(id=guild.id))
                logging.info(f"Synced {len(synced)} commands for guild {guild.id}")
        except Exception as e:
            logging.error(f"Failed to sync commands: {str(e)}")

    @commands.hybrid_command(name="requestcerts", description="Request a certification with a specified time.")
    async def requestcerts(self, ctx: commands.Context, time: str):
        try:
            if not ctx.guild:
                await ctx.send("This command can only be used in a server.", ephemeral=True)
                logging.error(f"requestcerts command attempted in DM by {ctx.author}")
                return
            view = CertRequestView(user=ctx.author, when=time)
            await ctx.send("Please select a certification from the dropdown below:", view=view, delete_after=60)
            logging.info(f"requestcerts command executed by {ctx.author} in guild {ctx.guild.id} with time: {time}")
        except Exception as e:
            logging.error(f"requestcerts command failed for {ctx.author} in guild {ctx.guild.id}: {str(e)}")
            await ctx.send(f"Error executing command: {str(e)}", ephemeral=True)

async def setup(bot):
    await bot.add_cog(CertificationRequests(bot))
    logging.info("CertificationRequests cog added to bot")
