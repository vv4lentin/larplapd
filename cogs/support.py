import discord
from discord.ext import commands
from discord import ui
import io
from datetime import datetime
import logging
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
SUPPORT_ROLES = {
    "general": 1339058176003407915,
    "ia": 1306381893515870209,
    "boc": 1361565373593292851,
    "botdev": 1337050305153470574  # SHR is also the directive role
}

CONFIG = {
    "panel_channel_id": 1292533788974387425,
    "transcript_channel_id": 1331018524218626100,
    "log_channel_id": 1331018524218626100,
    "ticket_prefixes": {
        "general": "g",
        "ia": "ia",
        "boc": "boc",
        "botdev": "botdev"
    },
    "max_tickets_per_user": 4,
    "ticket_categories": {  # New: Category IDs for each ticket type
        "general": 1376216650000633957,  # Replace with actual category ID for Support tickets
        "ia": 1376216515191509082,    # Replace with actual category ID for News tickets
        "boc": 1376216153256362044,    # Replace with actual category ID for Production tickets
        "botdev": 1376217124238000269      # Replace with actual category ID for SHR tickets
    }
}

class TicketActionView(ui.View):
    def __init__(self, cog, owner, ticket_type):
        super().__init__(timeout=None)
        self.cog = cog
        self.owner = owner
        self.ticket_type = ticket_type

    @ui.button(label="Claim", style=discord.ButtonStyle.primary, emoji="✅")
    async def claim(self, interaction: discord.Interaction, button: ui.Button):
        if not any(role.id in SUPPORT_ROLES.values() for role in interaction.user.roles):
            await interaction.response.send_message("You don't have permission to claim tickets.", ephemeral=True)
            return
        
        if self.cog.ticket_data[interaction.channel.id]["claimed_by"]:
            await interaction.response.send_message("This ticket is already claimed.", ephemeral=True)
            return

        self.cog.ticket_data[interaction.channel.id]["claimed_by"] = interaction.user
        self.cog.ticket_data[interaction.channel.id]["status"] = "claimed"
        await interaction.channel.edit(topic=f"Claimed by {interaction.user.name} | {self.ticket_type.title()}")
        await interaction.response.send_message(f"Ticket claimed by {interaction.user.mention}", ephemeral=False)
        await interaction.channel.send(f"{self.owner.mention} Your ticket has been claimed by {interaction.user.mention}")
        button.disabled = True
        await interaction.message.edit(view=self)
        await self.cog.log_action("claim", interaction.channel, interaction.user)

class CloseActionView(ui.View):
    def __init__(self, cog, owner, ticket_type):
        super().__init__(timeout=None)
        self.cog = cog
        self.owner = owner
        self.ticket_type = ticket_type

    @ui.button(label="Transcript", style=discord.ButtonStyle.primary, emoji="📜")
    async def transcript(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.defer()
        await self.cog.send_transcript(interaction.channel)
        await interaction.followup.send("Transcript sent.", ephemeral=True)

    @ui.button(label="Delete", style=discord.ButtonStyle.danger, emoji="🗑️")
    async def delete(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.send_message("Deleting ticket...", ephemeral=True)
        await interaction.channel.delete()
        await self.cog.log_action("delete", interaction.channel, interaction.user)

    @ui.button(label="Reopen", style=discord.ButtonStyle.success, emoji="🔄")
    async def reopen(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.channel.set_permissions(self.owner, read_messages=True, send_messages=True)
        self.cog.ticket_data[interaction.channel.id]["status"] = "open"
        await interaction.channel.edit(topic=f"Open | {self.ticket_type.title()}")
        await interaction.response.send_message("Ticket reopened.")
        await interaction.channel.send(f"{self.owner.mention} Your ticket has been reopened.")
        await self.cog.log_action("reopen", interaction.channel, interaction.user)
        await interaction.message.delete()

class SupportDropdown(ui.Select):
    def __init__(self, cog):
        self.cog = cog
        options = [
            discord.SelectOption(label="General Ticket", description="General support help", emoji="❓"),
            discord.SelectOption(label="Internals Affairs Ticket", description="Report an LAPD Officer", emoji="🚔"),
            discord.SelectOption(label="Board of Chiefs Ticket", description="Highly sensitive issues, important things.", emoji="👑"),
            discord.SelectOption(label="Bot Developpement Ticket", description="Report a bug", emoji="🤖")
        ]
        super().__init__(placeholder="Select ticket type...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        try:
            ticket_type = self.values[0].split()[0].lower()
            user_tickets = sum(1 for data in self.cog.ticket_data.values() if data["owner"].id == interaction.user.id)
            if user_tickets >= CONFIG["max_tickets_per_user"]:
                await interaction.response.send_message(
                    f"You've reached the maximum of {CONFIG['max_tickets_per_user']} open tickets.", 
                    ephemeral=True
                )
                return
            await self.cog.create_ticket(interaction, ticket_type)
        except Exception as e:
            logger.error(f"Error creating ticket: {str(e)}")
            await interaction.response.send_message("Failed to create ticket. Please try again.", ephemeral=True)

class SupportDropdownView(ui.View):
    def __init__(self, cog):
        super().__init__(timeout=None)
        self.add_item(SupportDropdown(cog))

class CloseRequestView(ui.View):
    def __init__(self, cog):
        super().__init__(timeout=None)
        self.cog = cog

    @ui.button(label="Close", style=discord.ButtonStyle.danger, emoji="🔒")
    async def close(self, interaction: discord.Interaction, button: ui.Button):
        await self.cog.close_ticket(interaction)

    @ui.button(label="Cancel", style=discord.ButtonStyle.secondary, emoji="❌")
    async def cancel(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.message.delete()
        await interaction.response.send_message("Close request canceled.", ephemeral=True)

class FoundershipRequestView(ui.View):
    def __init__(self, cog, requester):
        super().__init__(timeout=None)
        self.cog = cog
        self.requester = requester

    @ui.button(label="Accept", style=discord.ButtonStyle.success, emoji="✅")
    async def accept(self, interaction: discord.Interaction, button: ui.Button):
        await self.cog.handle_shr_request(interaction, self.requester, accept=True)

    @ui.button(label="Refuse", style=discord.ButtonStyle.danger, emoji="❌")
    async def refuse(self, interaction: discord.Interaction, button: ui.Button):
        await self.cog.handle_shr_request(interaction, self.requester, accept=False)

class Support(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.ticket_data = {}
        self.load_ticket_data()

    def load_ticket_data(self):
        try:
            with open("ticket_data.json", "r") as f:
                self.ticket_data = json.load(f)
        except FileNotFoundError:
            self.ticket_data = {}

    def save_ticket_data(self):
        with open("ticket_data.json", "w") as f:
            json.dump(self.ticket_data, f, default=str)

    async def create_ticket(self, interaction: discord.Interaction, ticket_type: str):
        prefix = CONFIG["ticket_prefixes"].get(ticket_type, ticket_type)
        channel_name = f"{prefix}-{interaction.user.name}-{datetime.now().strftime('%m%d%H%M')}"

        guild = interaction.guild
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }

        role_id = SUPPORT_ROLES.get(ticket_type)
        role_mention = ""
        if role_id:
            role = guild.get_role(role_id)
            if role:
                overwrites[role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)
                role_mention = role.mention

        # Get category for the ticket type
        category_id = CONFIG["ticket_categories"].get(ticket_type)
        category = None
        if category_id:
            category = guild.get_channel(category_id)
            if not isinstance(category, discord.CategoryChannel):
                logger.warning(f"Category ID {category_id} for {ticket_type} is not a valid category. Falling back to panel channel category.")
                category = None

        # Fallback to panel channel's category if specific category is invalid
        if not category:
            panel_channel = guild.get_channel(CONFIG["panel_channel_id"])
            if panel_channel and panel_channel.category:
                category = panel_channel.category
            else:
                logger.warning("No valid category found. Creating ticket without category.")

        try:
            channel = await guild.create_text_channel(
                name=channel_name,
                category=category,
                overwrites=overwrites
            )
        except Exception as e:
            logger.error(f"Error creating ticket channel: {str(e)}")
            await interaction.response.send_message("Failed to create ticket channel.", ephemeral=True)
            return

        self.ticket_data[channel.id] = {
            "owner": interaction.user,
            "type": ticket_type,
            "created_at": datetime.now().isoformat(),
            "claimed_by": None,
            "status": "open"
        }
        self.save_ticket_data()

        embed = discord.Embed(
            title=f"Los Angeles Police Department Support {ticket_type.upper()} Ticket",
            description="An officer will assist you soon. Please describe your issue. If you choose the wrong type of ticket, please do !close.",
            color=discord.Color.green(),
            timestamp=datetime.now()
        )
        embed.add_field(name="Ticket Type", value=ticket_type.title(), inline=True)
        embed.add_field(name="Created By", value=interaction.user.mention, inline=True)
        embed.add_field(name="Status", value="Open", inline=True)
        embed.set_footer(text=f"Ticket ID: {channel.id}")

        view = TicketActionView(self, interaction.user, ticket_type)
        content = f"{interaction.user.mention} {role_mention}".strip()
        await channel.send(content=content, embed=embed, view=view)
        await interaction.response.send_message(f"Ticket created: {channel.mention}", ephemeral=True)
        await channel.send(f"{interaction.user.mention} Your {ticket_type.upper()} ticket has been created.")
        await self.log_action("create", channel, interaction.user)

    async def send_transcript(self, channel):
        try:
            transcript = []
            async for message in channel.history(limit=None, oldest_first=True):
                timestamp = message.created_at.strftime("%Y-%m-%d %H:%M:%S")
                content = message.content or "[No content]"
                transcript.append(f"[{timestamp}] {message.author.display_name}: {content}")
            
            transcript_text = "\n".join(transcript)
            file = discord.File(fp=io.StringIO(transcript_text), filename=f"transcript-{channel.name}.txt")
            log_channel = self.bot.get_channel(CONFIG["transcript_channel_id"])
            
            if log_channel:
                embed = discord.Embed(
                    title=f"Transcript for {channel.name}",
                    color=discord.Color.blue(),
                    timestamp=datetime.now()
                )
                embed.add_field(name="Ticket ID", value=str(channel.id), inline=True)
                embed.add_field(name="Type", value=self.ticket_data.get(channel.id, {}).get("type", "Unknown"), inline=True)
                await log_channel.send(embed=embed, file=file)
            else:
                logger.error("Transcript channel not found")
        except Exception as e:
            logger.error(f"Error sending transcript: {str(e)}")

    async def close_ticket(self, interaction: discord.Interaction):
        channel = interaction.channel
        ticket_data = self.ticket_data.get(channel.id, {})
        owner = ticket_data.get("owner")
        claimer = ticket_data.get("claimed_by")

        # Reset permissions: only bot and claimer (if exists) retain access
        new_overwrites = {
            interaction.guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }
        if claimer:
            new_overwrites[claimer] = discord.PermissionOverwrite(read_messages=True, send_messages=True)

        try:
            await channel.edit(overwrites=new_overwrites)
        except Exception as e:
            logger.error(f"Error updating permissions on close: {str(e)}")
            await interaction.response.send_message("Error updating permissions.", ephemeral=True)
            return

        self.ticket_data[channel.id]["status"] = "closed"
        self.save_ticket_data()

        embed = discord.Embed(
            title="Ticket Closed",
            description="This ticket is closed. Choose an action below:",
            color=discord.Color.orange(),
            timestamp=datetime.now()
        )
        embed.add_field(name="Ticket ID", value=str(channel.id), inline=True)
        embed.add_field(name="Type", value=ticket_data.get("type", "Unknown"), inline=True)
        view = CloseActionView(self, owner, ticket_data.get("type"))
        await interaction.response.send_message(embed=embed, view=view)
        await channel.send(f"{owner.mention} Your ticket has been closed. {'Only the claimer retains access.' if claimer else 'All user access has been removed.'}")
        await self.log_action("close", channel, interaction.user, f"Claimer retained: {claimer.mention if claimer else 'None'}")

    async def handle_shr_request(self, interaction: discord.Interaction, requester: discord.Member, accept: bool):
        await interaction.response.defer()
        shr_role = interaction.guild.get_role(SUPPORT_ROLES["shr"])
        
        if not shr_role:
            await interaction.followup.send("SHR role not found.", ephemeral=True)
            return

        if accept:
            new_overwrites = {
                interaction.guild.default_role: discord.PermissionOverwrite(read_messages=False),
                interaction.guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True),
                requester: discord.PermissionOverwrite(read_messages=True, send_messages=True),
                shr_role: discord.PermissionOverwrite(read_messages=True, send_messages=True)
            }
            await interaction.channel.edit(overwrites=new_overwrites)
            self.ticket_data[interaction.channel.id]["status"] = "shr_restricted"
            self.save_ticket_data()
            await interaction.followup.send(f"SHR request accepted for {requester.mention}.", ephemeral=True)
            await interaction.channel.send(f"{requester.mention} SHR request accepted by {interaction.user.mention}.")
            await interaction.channel.send(f"{requester.mention} Your SHR request has been approved. Access restricted to SHR team.")
        else:
            await interaction.followup.send(f"SHR request refused for {requester.mention}.", ephemeral=True)
            await interaction.channel.send(f"{requester.mention} Your SHR request was denied.")
        
        await interaction.message.delete()
        await self.log_action("shr_request", interaction.channel, interaction.user, f"{'Accepted' if accept else 'Refused'}")

    async def log_action(self, action: str, channel: discord.TextChannel, user: discord.Member, extra: str = ""):
        log_channel = self.bot.get_channel(CONFIG["log_channel_id"])
        if log_channel:
            embed = discord.Embed(
                title=f"Ticket {action.capitalize()}",
                description=f"Action: {action}\nChannel: {channel.name}\nUser: {user.mention}\n{extra}",
                color=discord.Color.blue(),
                timestamp=datetime.now()
            )
            embed.add_field(name="Ticket ID", value=str(channel.id), inline=True)
            embed.add_field(name="Type", value=self.ticket_data.get(channel.id, {}).get("type", "Unknown"), inline=True)
            await log_channel.send(embed=embed)

    @commands.command()
    async def panel(self, ctx):
        try:
            embed = discord.Embed(
                title="Los Angeles Police Department Support",
                description="""
**General Support:** ❓
-> General questions and issues

**Internals Affairs Support:** 🚔
-> Report LAPD Officers

**Board of Chiefs Support:** 👑
-> Highly important issues that requires BOC
/!\ Do not open a BOC ticket for a minor issue /!\


**Bot Developpement Support:** 🤖
-> Report a bot bug or an issue with the bot.
""",
                color=discord.Color.blue(),
                timestamp=datetime.now()
            )
            view = SupportDropdownView(self)
            panel_channel = self.bot.get_channel(CONFIG["panel_channel_id"])
            if panel_channel:
                await panel_channel.send(embed=embed, view=view)
                await ctx.send(f"✅ Panel sent to {panel_channel.mention}", delete_after=5)
            else:
                await ctx.send("❌ Panel channel not found.", delete_after=5)
        except Exception as e:
            logger.error(f"Error sending panel: {str(e)}")
            await ctx.send("❌ Error creating panel.", delete_after=5)

    @commands.command()
    async def close(self, ctx):
        await self.close_ticket(ctx)

    @commands.command()
    async def add(self, ctx, member: discord.Member):
        try:
            await ctx.channel.set_permissions(member, read_messages=True, send_messages=True)
            await ctx.send(f"Added {member.mention} to the ticket.")
            await self.log_action("add", ctx.channel, ctx.author, f"Added {member.mention}")
        except Exception as e:
            logger.error(f"Error adding member: {str(e)}")
            await ctx.send("❌ Error adding member.", ephemeral=True)

    @commands.command()
    async def remove(self, ctx, member: discord.Member):
        try:
            await ctx.channel.set_permissions(member, overwrite=None)
            await ctx.send(f"Removed {member.mention} from the ticket.")
            await self.log_action("remove", ctx.channel, ctx.author, f"Removed {member.mention}")
        except Exception as e:
            logger.error(f"Error removing member: {str(e)}")
            await ctx.send("❌ Error removing member.", ephemeral=True)

    @commands.command()
    async def closerequest(self, ctx):
        embed = discord.Embed(
            title="Close Request",
            description="Confirm ticket closure:",
            color=discord.Color.orange(),
            timestamp=datetime.now()
        )
        view = CloseRequestView(self)
        await ctx.send(embed=embed, view=view)

    @commands.command()
    async def ticketstatus(self, ctx):
        if ctx.channel.id in self.ticket_data:
            ticket = self.ticket_data[ctx.channel.id]
            embed = discord.Embed(
                title=f"Ticket Status: {ctx.channel.name}",
                color=discord.Color.blue(),
                timestamp=datetime.now()
            )
            embed.add_field(name="Type", value=ticket["type"].title(), inline=True)
            embed.add_field(name="Status", value=ticket["status"].title(), inline=True)
            embed.add_field(name="Owner", value=ticket["owner"].mention, inline=True)
            embed.add_field(name="Created", value=ticket["created_at"], inline=True)
            embed.add_field(name="Claimed By", value=ticket["claimed_by"].mention if ticket["claimed_by"] else "Unclaimed", inline=True)
            await ctx.send(embed=embed)
        else:
            if any(role.id in SUPPORT_ROLES.values() for role in ctx.author.roles):
                embed = discord.Embed(
                    title="All Active Tickets",
                    color=discord.Color.blue(),
                    timestamp=datetime.now()
                )
                for ticket_id, ticket in self.ticket_data.items():
                    channel = self.bot.get_channel(int(ticket_id))
                    if channel:
                        embed.add_field(
                            name=f"{channel.name}",
                            value=f"Type: {ticket['type'].title()}\nStatus: {ticket['status'].title()}\nOwner: {ticket['owner'].mention}",
                            inline=False
                        )
                if not embed.fields:
                    embed.description = "No active tickets."
                await ctx.send(embed=embed)
            else:
                await ctx.send("You can only check the status of your own ticket.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Support(bot))
