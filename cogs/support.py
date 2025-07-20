import discord
from discord.ext import commands
from discord import ui
import io
from datetime import datetime
import logging
import traceback

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
SUPPORT_ROLES = {
    "general": 1306382245895868476,
    "ia": 1306381893515870209,
    "boc": 1361565373593292851,
    "botdev": 1337050305153470574
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
    "ticket_categories": {
        "general": 1376216650000633957,
        "ia": 1376216515191509082,
        "boc": 1376216153256362044,
        "botdev": 1376217124238000269
    }
}

# Mapping for ticket types to display names
TICKET_TYPE_MAPPING = {
    "general": {"display": "General Ticket", "description": "General support help", "emoji": "❓"},
    "ia": {"display": "Internal Affairs Ticket", "description": "Report an LAPD Officer", "emoji": "🚔"},
    "boc": {"display": "Board of Chiefs", "description": "Highly sensitive issues, important things", "emoji": "👑"},
    "botdev": {"display": "Bot Development Ticket", "description": "Report a bug", "emoji": "🤖"}
}

class TicketActionView(ui.View):
    def __init__(self, cog, ticket_data):
        super().__init__(timeout=None)
        self.cog = cog
        self.owner = ticket_data["owner"]
        self.ticket_type = ticket_data["type"]

    @ui.button(label="Claim", style=discord.ButtonStyle.primary, emoji="✅")
    async def claim(self, interaction: discord.Interaction, button: ui.Button):
        if not any(role.id in SUPPORT_ROLES.values() for role in interaction.user.roles):
            await interaction.response.send_message("You don't have permission to claim tickets.", ephemeral=True)
            return
        
        if self.cog.ticket_data[interaction.channel.id]["claimed_by"]:
            await interaction.response.send_message("This is already claimed.", ephemeral=True)
            return

        self.cog.ticket_data[interaction.channel.id]["claimed_by"] = interaction.user
        self.cog.ticket_data[interaction.channel.id]["status"] = "claimed"
        prefix = CONFIG["ticket_prefixes"].get(self.ticket_type, self.ticket_type)
        await interaction.channel.edit(
            name=f"🟢-{prefix}-{self.owner.name.lower()}",
            topic=f"Claimed by {interaction.user.display_name} | {TICKET_TYPE_MAPPING[self.ticket_type]['display']}"
        )
        embed = discord.Embed(
            title="Ticket Claimed",
            description=f"Ticket claimed by {interaction.user.mention}",
            color=discord.Color.green(),
            timestamp=datetime.now()
        )
        await interaction.response.send_message(embed=embed)
        button.disabled = True
        await interaction.message.edit(view=self)
        await self.cog.log_action("claim", interaction.user, interaction.channel, f"Claimed by {interaction.user.display_name}")

    @ui.button(label="Close", style=discord.ButtonStyle.danger, emoji="🔒")
    async def close(self, interaction: discord.Interaction, button: ui.Button):
        await self.cog.close_ticket(interaction, reason="Closed via button")

class CloseActionView(ui.View):
    def __init__(self, cog, ticket_data):
        super().__init__(timeout=None)
        self.cog = cog
        self.owner = ticket_data["owner"]
        self.ticket_type = ticket_data["type"]

    @ui.button(label="Transcript", style=discord.ButtonStyle.primary, emoji="📜")
    async def transcript(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.defer()
        await self.cog.send_transcript(interaction.channel)
        await interaction.followup.send("Transcript sent.", ephemeral=True)

    @ui.button(label="Delete", style=discord.ButtonStyle.danger, emoji="🗑️")
    async def delete(self, interaction: discord.Interaction, button: ui.Button):
        embed = discord.Embed(
            title="Ticket Deletion",
            description="Deleting ticket...",
            color=discord.Color.red(),
            timestamp=datetime.now()
        )
        await interaction.response.send_message(embed=embed)
        await self.cog.log_action("delete", interaction.user, interaction.channel, "Ticket deleted")
        await interaction.channel.delete()

    @ui.button(label="Reopen", style=discord.ButtonStyle.success, emoji="🔄")
    async def reopen(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.channel.edit_permissions(self.owner, read_messages=True, send_messages=True)
        self.cog.ticket_data[interaction.channel.id]["status"] = "open"
        prefix = CONFIG["ticket_prefixes"].get(self.ticket_type, self.ticket_type)
        await interaction.channel.edit(
            name=f"🔴-{prefix}-{self.owner.name.lower()}",
            topic=f"Open | {TICKET_TYPE_MAPPING[self.ticket_type]['display']}"
        )
        embed = discord.Embed(
            title="Ticket Reopened",
            description="Ticket has been reopened.",
            color=discord.Color.green(),
            timestamp=datetime.now()
        )
        await interaction.response.send_message(embed=embed)
        await interaction.channel.send(f"{self.owner.mention} Your {TICKET_TYPE_MAPPING[self.ticket_type]['display']} ticket has been reopened.")
        await self.cog.log_action("reopen", interaction.user, interaction.channel, "Ticket reopened")
        await interaction.message.delete()

class TicketReasonModal(ui.Modal, title="Ticket Creation Reason"):
    def __init__(self, cog, ticket_type):
        super().__init__()
        self.cog = cog
        self.ticket_type = ticket_type
        self.reason = ui.TextInput(
            label="Reason for Opening Ticket",
            placeholder="Enter the reason for creating this ticket...",
            style=discord.TextStyle.paragraph,
            required=True
        )
        self.add_item(self.reason)

    async def on_submit(self, interaction: discord.Interaction):
        await self.cog.create_ticket(interaction, self.ticket_type, self.reason.value)

class SupportDropdown(ui.Select):
    def __init__(self, cog):
        self.cog = cog
        options = [
            discord.SelectOption(
                label=TICKET_TYPE_MAPPING["general"]["display"],
                description=TICKET_TYPE_MAPPING["general"]["description"],
                emoji=TICKET_TYPE_MAPPING["general"]["emoji"],
                value="general"
            ),
            discord.SelectOption(
                label=TICKET_TYPE_MAPPING["ia"]["display"],
                description=TICKET_TYPE_MAPPING["ia"]["description"],
                emoji=TICKET_TYPE_MAPPING["ia"]["emoji"],
                value="ia"
            ),
            discord.SelectOption(
                label=TICKET_TYPE_MAPPING["boc"]["display"],
                description=TICKET_TYPE_MAPPING["boc"]["description"],
                emoji=TICKET_TYPE_MAPPING["boc"]["emoji"],
                value="boc"
            ),
            discord.SelectOption(
                label=TICKET_TYPE_MAPPING["botdev"]["display"],
                description=TICKET_TYPE_MAPPING["botdev"]["description"],
                emoji=TICKET_TYPE_MAPPING["botdev"]["emoji"],
                value="botdev"
            )
        ]
        super().__init__(placeholder="Select ticket type...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        try:
            ticket_type = self.values[0]
            user_tickets = sum(1 for data in self.cog.ticket_data.values() if data.get("owner") and data.get("owner").id == interaction.user.id)
            if user_tickets >= CONFIG["max_tickets_per_user"]:
                embed = discord.Embed(
                    title="Ticket Limit Reached",
                    description=f"You've reached the maximum of {CONFIG['max_tickets_per_user']} open tickets.",
                    color=discord.Color.red(),
                    timestamp=datetime.now()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            await interaction.response.send_modal(TicketReasonModal(self.cog, ticket_type))
        except Exception as e:
            logger.error(f"Error in dropdown callback: {str(e)}\n{traceback.format_exc()}")
            embed = discord.Embed(
                title="Error",
                description="Failed to process ticket creation. Please try again.",
                color=discord.Color.red(),
                timestamp=datetime.now()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

class SupportDropdownView(ui.View):
    def __init__(self, cog):
        super().__init__(timeout=None)
        self.cog = cog
        self.add_item(SupportDropdown(cog))

class CloseRequestView(ui.View):
    def __init__(self, cog):
        super().__init__(timeout=None)
        self.cog = cog
        self.reason_modal = CloseReasonModal(cog)

    @ui.button(label="Close", style=discord.ButtonStyle.danger, emoji="🔒")
    async def close(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.send_modal(self.reason_modal)

    @ui.button(label="Cancel", style=discord.ButtonStyle.secondary, emoji="❌")
    async def cancel(self, interaction: discord.Interaction, button: ui.Button):
        embed = discord.Embed(
            title="Close Request Cancelled",
            description="Close request cancelled.",
            color=discord.Color.greyple(),
            timestamp=datetime.now()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        await interaction.message.delete()

class CloseReasonModal(ui.Modal, title="Close Ticket"):
    def __init__(self, cog):
        super().__init__()
        self.cog = cog
        self.reason = ui.TextInput(
            label="Reason for Closing",
            placeholder="Enter the reason for closing the ticket...",
            style=discord.TextStyle.paragraph,
            required=True
        )
        self.add_item(self.reason)

    async def on_submit(self, interaction: discord.Interaction):
        await self.cog.close_ticket(interaction, reason=self.reason.value)

class Support(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.ticket_data = {}  # In-memory storage, no JSON

    async def create_ticket(self, interaction: discord.Interaction, ticket_type: str, reason: str):
        if ticket_type not in TICKET_TYPE_MAPPING:
            embed = discord.Embed(
                title="Error",
                description="Invalid ticket type.",
                color=discord.Color.red(),
                timestamp=datetime.now()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        prefix = CONFIG["ticket_prefixes"].get(ticket_type, ticket_type)
        # Sanitize channel name to ensure it's valid (2-100 characters)
        channel_name = f"🔴-{prefix}-{interaction.user.name.lower()}"[:100]
        if len(channel_name) < 2:
            channel_name = f"🔴-{prefix}-ticket"

        guild = interaction.guild
        if not guild:
            logger.error("Guild not found for interaction.")
            embed = discord.Embed(
                title="Error",
                description="Guild not found.",
                color=discord.Color.red(),
                timestamp=datetime.now()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        # Check bot permissions
        bot_member = guild.get_member(self.bot.user.id)
        if not bot_member:
            logger.error("Bot member not found in guild.")
            embed = discord.Embed(
                title="Error",
                description="Bot not found in guild.",
                color=discord.Color.red(),
                timestamp=datetime.now()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        if not bot_member.guild_permissions.manage_channels:
            logger.error("Bot lacks manage_channels permission.")
            embed = discord.Embed(
                title="Error",
                description="Bot lacks permission to create channels.",
                color=discord.Color.red(),
                timestamp=datetime.now()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

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
            else:
                logger.warning(f"Role ID {role_id} for {ticket_type} not found.")

        category_id = CONFIG["ticket_categories"].get(ticket_type)
        category = None
        if category_id:
            category = guild.get_channel(category_id)
            if not isinstance(category, discord.CategoryChannel):
                logger.warning(f"Category ID {category_id} for {ticket_type} is not a valid category.")
                category = None

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
        except discord.errors.Forbidden as e:
            logger.error(f"Permission error creating ticket channel: {str(e)}\n{traceback.format_exc()}")
            embed = discord.Embed(
                title="Error",
                description="Bot lacks permission to create channel.",
                color=discord.Color.red(),
                timestamp=datetime.now()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        except discord.errors.HTTPException as e:
            logger.error(f"HTTP error creating ticket channel: {str(e)}\n{traceback.format_exc()}")
            embed = discord.Embed(
                title="Error",
                description=f"Error creating ticket channel: {str(e)}",
                color=discord.Color.red(),
                timestamp=datetime.now()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        except Exception as e:
            logger.error(f"Unexpected error creating ticket channel: {str(e)}\n{traceback.format_exc()}")
            embed = discord.Embed(
                title="Error",
                description="Failed to create ticket channel. Please try again.",
                color=discord.Color.red(),
                timestamp=datetime.now()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        # Store ticket data
        self.ticket_data[channel.id] = {
            "owner": interaction.user,
            "type": ticket_type,
            "created_at": datetime.now().isoformat(),
            "claimed_by": None,
            "status": "open",
            "reason": reason
        }

        embed = discord.Embed(
            title=f"Los Angeles Police Department | {TICKET_TYPE_MAPPING[ticket_type]['display']}",
            description="An officer will assist you soon. Please describe your issue. If you chose the wrong ticket type, use the Close button or `!close`.",
            color=discord.Color.green(),
            timestamp=datetime.now()
        )
        embed.add_field(name="Ticket Type", value=TICKET_TYPE_MAPPING[ticket_type]["display"], inline=True)
        embed.add_field(name="Created By", value=interaction.user.mention, inline=True)
        embed.add_field(name="Status", value="Open", inline=True)
        embed.add_field(name="Reason", value=reason, inline=False)

        view = TicketActionView(self, self.ticket_data[channel.id])
        content = f"{interaction.user.mention} {role_mention}".strip()
        try:
            await channel.send(content=content, embed=embed, view=view)
            embed = discord.Embed(
                title="Ticket Created",
                description=f"Ticket created: {channel.mention}",
                color=discord.Color.green(),
                timestamp=datetime.now()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            await self.log_action("create", interaction.user, channel, f"Type: {TICKET_TYPE_MAPPING[ticket_type]['display']} | Reason: {reason}")
        except Exception as e:
            logger.error(f"Error sending ticket creation message: {str(e)}\n{traceback.format_exc()}")
            embed = discord.Embed(
                title="Partial Success",
                description="Ticket created, but failed to send initial message.",
                color=discord.Color.yellow(),
                timestamp=datetime.now()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

    async def send_transcript(self, channel):
        try:
            transcript = []
            async for message in channel.history(limit=None, oldest_first=True):
                timestamp = message.created_at.strftime("%Y-%m-%d %H:%M:%S")
                content = message.content or "[No content]"
                transcript.append(f"[{timestamp}] {message.author.display_name}: {content}")

            transcript_text = "\n".join(transcript)
            file = discord.File(io.StringIO(transcript_text), filename=f"transcript-{channel.name}.txt")
            log_channel = self.bot.get_channel(CONFIG["transcript_channel_id"])

            if log_channel:
                embed = discord.Embed(
                    title=f"Transcript for {channel.name}",
                    color=discord.Color.blue(),
                    timestamp=datetime.now()
                )
                ticket_type = self.ticket_data.get(channel.id, {}).get("type", "Unknown")
                embed.add_field(name="Type", value=TICKET_TYPE_MAPPING.get(ticket_type, {}).get("display", "Unknown"), inline=True)
                await log_channel.send(embed=embed, file=file)
            else:
                logger.error("Transcript channel not found")
        except Exception as e:
            logger.error(f"Error sending transcript: {str(e)}\n{traceback.format_exc()}")

    async def close_ticket(self, interaction: discord.Interaction, reason: str):
        channel = interaction.channel
        ticket_data = self.ticket_data.get(channel.id, {})
        if not ticket_data:
            embed = discord.Embed(
                title="Error",
                description="This channel is not a registered ticket.",
                color=discord.Color.red(),
                timestamp=datetime.now()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        owner = ticket_data.get("owner")
        claimer = ticket_data.get("claimed_by")
        ticket_type = ticket_data.get("type", "unknown")

        prefix = CONFIG["ticket_prefixes"].get(ticket_type, ticket_type)
        try:
            await channel.edit(name=f"🔒-{prefix}-{owner.name.lower()}"[:100])
        except Exception as e:
            logger.error(f"Error updating channel name on close: {str(e)}\n{traceback.format_exc()}")

        new_overwrites = {
            interaction.guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }
        if claimer:
            new_overwrites[claimer] = discord.PermissionOverwrite(read_messages=True, send_messages=True)

        try:
            await channel.edit(overwrites=new_overwrites)
        except Exception as e:
            logger.error(f"Error updating permissions on close: {str(e)}\n{traceback.format_exc()}")
            embed = discord.Embed(
                title="Error",
                description="Error updating permissions.",
                color=discord.Color.red(),
                timestamp=datetime.now()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        self.ticket_data[channel.id]["status"] = "closed"

        embed = discord.Embed(
            title="Ticket Closed",
            description=f"This ticket is closed. Reason: {reason}\nChoose an action below:",
            color=discord.Color.orange(),
            timestamp=datetime.now()
        )
        embed.add_field(name="Type", value=TICKET_TYPE_MAPPING.get(ticket_type, {}).get("display", "Unknown"), inline=True)
        view = CloseActionView(self, ticket_data)
        await interaction.response.send_message(embed=embed, view=view)
        await self.log_action("close", interaction.user, channel, f"Reason: {reason} | Claimer retained: {claimer.mention if claimer else 'None'}")

    async def log_action(self, action: str, user: discord.Member, channel: discord.TextChannel, extra: str = ""):
        log_channel = self.bot.get_channel(CONFIG["log_channel_id"])
        if log_channel:
            embed = discord.Embed(
                title=f"Ticket {action.capitalize()}",
                description=f"Action: {action}\nChannel: {channel.name}\nUser: {user.mention}\n{extra}",
                color=discord.Color.blue(),
                timestamp=datetime.now()
            )
            ticket_type = self.ticket_data.get(channel.id, {}).get("type", "Unknown")
            embed.add_field(name="Type", value=TICKET_TYPE_MAPPING.get(ticket_type, {}).get("display", "Unknown"), inline=True)
            try:
                await log_channel.send(embed=embed)
            except Exception as e:
                logger.error(f"Error sending log message: {str(e)}\n{traceback.format_exc()}")

    @commands.command()
    async def ticketpanel(self, ctx: commands.Context):
        try:
            embed = discord.Embed(
                title="Los Angeles Police Department Support",
                description="""
**General Ticket:** ❓
-> General questions and issues

**Internal Affairs Ticket:** 🚔
-> Report LAPD Officers

**Board of Chiefs Ticket:** 👑
-> Highly important issues that require BOC
/!\ Do not open a BOC ticket for a minor issue /!\

**Bot Development Ticket:** 🤖
-> Report a bot bug or an issue with the bot
""",
                color=discord.Color.blue(),
                timestamp=datetime.now()
            )
            view = SupportDropdownView(self)
            panel_channel = self.bot.get_channel(CONFIG["panel_channel_id"])
            if panel_channel:
                await panel_channel.send(embed=embed, view=view)
                embed = discord.Embed(
                    title="Success",
                    description=f"Panel sent to {panel_channel.mention}",
                    color=discord.Color.green(),
                    timestamp=datetime.now()
                )
                await ctx.send(embed=embed, delete_after=5)
            else:
                logger.error("Panel channel not found")
                embed = discord.Embed(
                    title="Error",
                    description="Panel channel not found.",
                    color=discord.Color.red(),
                    timestamp=datetime.now()
                )
                await ctx.send(embed=embed, delete_after=5)
        except Exception as e:
            logger.error(f"Error sending panel: {str(e)}\n{traceback.format_exc()}")
            embed = discord.Embed(
                title="Error",
                description="Error creating panel.",
                color=discord.Color.red(),
                timestamp=datetime.now()
            )
            await ctx.send(embed=embed, delete_after=5)

    @commands.command()
    async def close(self, ctx: commands.Context):
        ticket_data = self.ticket_data.get(ctx.channel.id, {})
        if not ticket_data:
            embed = discord.Embed(
                title="Error",
                description="This channel is not a registered ticket.",
                color=discord.Color.red(),
                timestamp=datetime.now()
            )
            await ctx.send(embed=embed)
            return
        embed = discord.Embed(
            title="Close Request",
            description="Confirm ticket closure by providing a reason:",
            color=discord.Color.orange(),
            timestamp=datetime.now()
        )
        view = CloseRequestView(self)
        await ctx.send(embed=embed, view=view)

    @commands.command()
    async def add(self, ctx: commands.Context, member: discord.Member):
        ticket_data = self.ticket_data.get(ctx.channel.id, {})
        if not ticket_data:
            embed = discord.Embed(
                title="Error",
                description="This channel is not a registered ticket.",
                color=discord.Color.red(),
                timestamp=datetime.now()
            )
            await ctx.send(embed=embed)
            return
        if ticket_data["status"] == "closed":
            embed = discord.Embed(
                title="Error",
                description="This ticket is closed and cannot have members added.",
                color=discord.Color.red(),
                timestamp=datetime.now()
            )
            await ctx.send(embed=embed)
            return
        try:
            await ctx.channel.set_permissions(member, read_messages=True, send_messages=True)
            embed = discord.Embed(
                title="Member Added",
                description=f"Added {member.mention} to the ticket.",
                color=discord.Color.green(),
                timestamp=datetime.now()
            )
            await ctx.send(embed=embed)
            await self.log_action("add", ctx.author, ctx.channel, f"Added {member.mention}")
        except discord.errors.Forbidden:
            logger.error(f"Bot lacks permission to add {member} to channel {ctx.channel.name}")
            embed = discord.Embed(
                title="Error",
                description="Bot lacks permission to add members to this channel.",
                color=discord.Color.red(),
                timestamp=datetime.now()
            )
            await ctx.send(embed=embed)
        except Exception as e:
            logger.error(f"Error adding member {member} to channel {ctx.channel.name}: {str(e)}\n{traceback.format_exc()}")
            embed = discord.Embed(
                title="Error",
                description=f"Error adding member: {str(e)}",
                color=discord.Color.red(),
                timestamp=datetime.now()
            )
            await ctx.send(embed=embed)

    @commands.command()
    async def remove(self, ctx: commands.Context, member: discord.Member):
        ticket_data = self.ticket_data.get(ctx.channel.id, {})
        if not ticket_data:
            embed = discord.Embed(
                title="Error",
                description="This channel is not a registered ticket.",
                color=discord.Color.red(),
                timestamp=datetime.now()
            )
            await ctx.send(embed=embed)
            return
        if ticket_data["status"] == "closed":
            embed = discord.Embed(
                title="Error",
                description="This ticket is closed and cannot have members removed.",
                color=discord.Color.red(),
                timestamp=datetime.now()
            )
            await ctx.send(embed=embed)
            return
        if member == ticket_data.get("owner"):
            embed = discord.Embed(
                title="Error",
                description="You cannot remove the ticket owner.",
                color=discord.Color.red(),
                timestamp=datetime.now()
            )
            await ctx.send(embed=embed)
            return
        if member == ticket_data.get("claimed_by"):
            embed = discord.Embed(
                title="Error",
                description="You cannot remove the ticket claimer.",
                color=discord.Color.red(),
                timestamp=datetime.now()
            )
            await ctx.send(embed=embed)
            return
        try:
            await ctx.channel.set_permissions(member, read_messages=False, send_messages=False)
            embed = discord.Embed(
                title="Member Removed",
                description=f"Removed {member.mention} from the ticket.",
                color=discord.Color.green(),
                timestamp=datetime.now()
            )
            await ctx.send(embed=embed)
            await self.log_action("remove", ctx.author, ctx.channel, f"Removed {member.mention}")
        except discord.errors.Forbidden:
            logger.error(f"Bot lacks permission to remove {member} from channel {ctx.channel.name}")
            embed = discord.Embed(
                title="Error",
                description="Bot lacks permission to remove members from this channel.",
                color=discord.Color.red(),
                timestamp=datetime.now()
            )
            await ctx.send(embed=embed)
        except Exception as e:
            logger.error(f"Error removing member {member} from channel {ctx.channel.name}: {str(e)}\n{traceback.format_exc()}")
            embed = discord.Embed(
                title="Error",
                description=f"Error removing member: {str(e)}",
                color=discord.Color.red(),
                timestamp=datetime.now()
            )
            await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Support(bot))
