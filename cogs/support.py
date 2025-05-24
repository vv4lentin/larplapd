import discord
from discord.ext import commands
from discord import ui
import io

# Configure support roles by ID here
SUPPORT_ROLES = {
    "general": 1339058176003407915,    # Replace with actual role IDs
    "ia": 1306381893515870209,
    "botdev": 1337050305153470574,
    "boc": 1361565373593292851
}

# Set your panel channel ID here
PANEL_CHANNEL_ID = 1292533788974387425  # Replace with your actual panel channel ID
# Set your transcript channel ID here
TRANSCRIPT_CHANNEL_ID = 1375982365960306729 # Replace with your actual transcript channel ID

TICKET_PREFIX = {
    "general": "g",
    "ia": "ia",
    "botdev": "botdev",
    "boc": "boc"
}

class TicketActionView(ui.View):
    def __init__(self, cog, owner):
        super().__init__(timeout=None)
        self.cog = cog
        self.owner = owner

    @ui.button(label="Transcript", style=discord.ButtonStyle.primary)
    async def transcript(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.defer()
        await self.cog.send_transcript(interaction.channel)
        await interaction.followup.send("Transcript has been sent.", ephemeral=True)

    @ui.button(label="Delete", style=discord.ButtonStyle.danger)
    async def delete(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.send_message("Deleting the ticket…", ephemeral=True)
        await interaction.channel.delete()

    @ui.button(label="Open", style=discord.ButtonStyle.success)
    async def reopen(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.channel.set_permissions(self.owner, read_messages=True, send_messages=True)
        await interaction.response.send_message("Ticket reopened.")
        await interaction.message.delete()

class SupportDropdown(ui.Select):
    def __init__(self, cog):
        self.cog = cog
        options = [
            discord.SelectOption(label="General Ticket", description="General support help"),
            discord.SelectOption(label="Internals Affairs Ticket", description="Hockey's Corp News Division"),
            discord.SelectOption(label="Bot Developpement Ticket", description="Hockey's Corp Production Division"),
            discord.SelectOption(label="Board of Chiefs Ticket", description="Highly sensitive issues requiring SHR Team")
        ]
        super().__init__(placeholder="Choose your ticket type…", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        ticket_type = self.values[0].split()[0].lower()
        prefix = TICKET_PREFIX.get(ticket_type, ticket_type)
        channel_name = f"{prefix}-{interaction.user.name}"

        category = interaction.channel.category
        guild = interaction.guild
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }

        role_id = SUPPORT_ROLES.get(ticket_type)
        role_mention = ""
        if role_id:
            role = guild.get_role(role_id)
            if role:
                overwrites[role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)
                role_mention = role.mention

        channel = await guild.create_text_channel(name=channel_name, category=category, overwrites=overwrites)

        embed = discord.Embed(
            title=f"LAPD Support ({ticket_type.upper()})",
            description="An LAPD officer will be with you shortly. Please describe your issue. If you choose the wrong type of ticket, please close this one.",
            color=discord.Color.green()
        )
        content = f"{interaction.user.mention} {role_mention}".strip()
        await channel.send(content=content, embed=embed)
        await interaction.response.send_message(f"Your ticket has been created here: {channel.mention}", ephemeral=True)

class SupportDropdownView(ui.View):
    def __init__(self, cog):
        super().__init__(timeout=None)
        self.add_item(SupportDropdown(cog))

class CloseRequestView(ui.View):
    def __init__(self, cog):
        super().__init__(timeout=None)
        self.cog = cog

    @ui.button(label="Close", style=discord.ButtonStyle.danger)
    async def close(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.send_message("Closing the ticket…", ephemeral=True)

        channel = interaction.channel
        member = channel.overwrites.keys()
        owner = None
        for m in member:
            if isinstance(m, discord.Member) and m != interaction.guild.me:
                owner = m
                break

        if owner:
            await channel.set_permissions(owner, overwrite=None)

        embed = discord.Embed(title="Ticket Closed", description="This ticket has been closed. You may choose to reopen the ticket, delete the ticket, or send the transcript. You can choose mutliples choices.", color=discord.Color.orange())
        view = TicketActionView(self.cog, owner)
        await channel.send(embed=embed, view=view)

    @ui.button(label="Cancel", style=discord.ButtonStyle.secondary)
    async def dont_close(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.message.delete()
        await interaction.response.send_message("Close request canceled.", ephemeral=True)

class FoundershipRequestView(ui.View):
    def __init__(self, cog, requester):
        super().__init__(timeout=None)
        self.cog = cog
        self.requester = requester

    @ui.button(label="Accept", style=discord.ButtonStyle.success)
    async def accept(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.defer()
        
        channel = interaction.channel
        directive_role = interaction.guild.get_role(SUPPORT_ROLES["directive"])
        
        # Reset all permissions except for the bot
        new_overwrites = {
            interaction.guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            self.requester: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            directive_role: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }
        
        # Apply new permissions
        await channel.edit(overwrites=new_overwrites)

        await interaction.followup.send(f"SHR request accepted for {self.requester.mention}. Access restricted to {self.requester.mention} and {directive_role.mention}.", ephemeral=True)
        await channel.send(f"{self.requester.mention} SHR request has been accepted by {interaction.user.mention}. Only {directive_role.mention} and {self.requester.mention} have access.")
        await interaction.message.delete()  # Remove the request message

    @ui.button(label="Refuse", style=discord.ButtonStyle.danger)
    async def refuse(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.send_message(f"SHR request refused for {self.requester.mention}.", ephemeral=True)
        await interaction.message.delete()

class Support(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def send_transcript(self, channel):
        transcript = []
        async for message in channel.history(limit=None, oldest_first=True):
            transcript.append(f"{message.author.display_name}: {message.content}")
        transcript_text = "\n".join(transcript)
        file = discord.File(fp=io.StringIO(transcript_text), filename="transcript.txt")
        log_channel = self.bot.get_channel(TRANSCRIPT_CHANNEL_ID)
        if log_channel:
            await log_channel.send(content=f"Transcript for {channel.name}", file=file)

    @commands.command()
    async def panel(self, ctx):
        embed = discord.Embed(
            title="Hockey's Corporation Support",
            description="""
**General Support:**
-> Any questions or issues about all divisions.

**Internals Affairs Support:**
-> Report a LAPD Officer

**Bot Developpement Support:**
-> Any issues or questions about the Bot.
-> Report a Bug.

**Board of Chiefs Support:**
-> Highly sensitive issues requiring Board of Chief.
/!\ Do not open this type of ticket for a minor issue or a question. /!\
""",
            color=discord.Color.blue()
        )
        view = SupportDropdownView(self)
        panel_channel = self.bot.get_channel(PANEL_CHANNEL_ID)
        if panel_channel:
            await panel_channel.send(embed=embed, view=view)
            await ctx.send(f"✅ Panel sent to {panel_channel.mention}", delete_after=5)
        else:
            await ctx.send("❌ Panel channel not found. Check the channel ID.", delete_after=5)

    @commands.command()
    async def close(self, ctx):
        channel = ctx.channel
        member = channel.overwrites.keys()
        owner = None
        for m in member:
            if isinstance(m, discord.Member) and m != ctx.guild.me:
                owner = m
                break

        if owner:
            await channel.set_permissions(owner, overwrite=None)

        embed = discord.Embed(title="Ticket Closed", description="This ticket has been closed. You may choose to reopen the ticket, delete the ticket, or send the transcript. You can choose mutliples options.", color=discord.Color.orange())
        view = TicketActionView(self, owner)
        await ctx.send(embed=embed, view=view)

    @commands.command()
    async def add(self, ctx, member: discord.Member):
        await ctx.channel.set_permissions(member, read_messages=True, send_messages=True)
        await ctx.send(f"Added {member.mention} to the ticket.")

    @commands.command()
    async def remove(self, ctx, member: discord.Member):
        await ctx.channel.set_permissions(member, overwrite=None)
        await ctx.send(f"Removed {member.mention} from the ticket.")

    @commands.command()
    async def closerequest(self, ctx):
        embed = discord.Embed(
            title="Close Request", description="Do you want to close this ticket?", color=discord.Color.orange()
        )
        view = CloseRequestView(self)
        await ctx.send(embed=embed, view=view)

    @commands.command()
    async def requestboc(self, ctx):
        directive_role = ctx.guild.get_role(SUPPORT_ROLES["directive"])
        if not directive_role:
            await ctx.send("BOC role not found. Please check the configuration.")
            return

        embed = discord.Embed(
            title="BOC Request",
            description=f"{ctx.author.mention} has requested Board of Chiefs in this ticket ({ctx.channel.mention}).",
            color=discord.Color.purple()
        )
        view = FoundershipRequestView(self, ctx.author)
        await ctx.send(content=f"{directive_role.mention}", embed=embed, view=view)

async def setup(bot):
    await bot.add_cog(Support(bot))
