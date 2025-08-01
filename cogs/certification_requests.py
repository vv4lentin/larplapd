import discord
from discord import Embed, Colour, ButtonStyle, Interaction, Member, app_commands, Activity, ActivityType, Status
from discord.ui import Button, View, Select
from discord.ext import commands
import logging
from datetime import datetime, timezone
from typing import List

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s: %(message)s"
)
logger = logging.getLogger(__name__)

FTO_ROLE_ID = 1306458665410236436

CONFIG = {
    "GUILD_IDS": [1292523481539543193],  
    "REQUEST_CHANNEL_ID": 1383124547900936242,  
    "STATUS_CHANNEL_ID": 1304472122646859797,  
    "ALLOWED_ROLE_ID": None,  
    "THUMBNAIL_URL": "https://example.com/thumbnail.png"
}

class TrainingCertActionView(View):
    def __init__(self, user: Member, certification: str, original_message: discord.Message, history: List[str]):
        super().__init__(timeout=None) 
        self.user = user
        self.certification = certification
        self.original_message = original_message
        self.history = history

    @discord.ui.button(label="Accept", style=ButtonStyle.green)
    async def accept_button(self, interaction: Interaction, button: Button):
        channel = interaction.client.get_channel(CONFIG["STATUS_CHANNEL_ID"])
        if not channel:
            logger.error(f"Target channel {CONFIG['STATUS_CHANNEL_ID']} not found")
            await interaction.response.send_message("Error: Status channel not found.", ephemeral=True)
            return

        self.history.append(f"✅ Accepted by {interaction.user.display_name} at {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
        embed = Embed(
            title="Certification Training Request",
            description="**Status: Accepted ✅**",
            color=Colour.green(),
            timestamp=datetime.now(timezone.utc)
        )
        embed.add_field(name="User", value=f"{self.user.mention} ({self.user.id})", inline=False)
        embed.add_field(name="Training Certification", value=self.certification, inline=False)
        embed.add_field(name="When", value=self.original_message.embeds[0].fields[2].value, inline=False)
        embed.add_field(name="Status History", value="\n".join(self.history), inline=False)
        embed.set_thumbnail(url=CONFIG["THUMBNAIL_URL"])
        embed.set_footer(text=f"Requested by {self.user.display_name}")

        status_embed = Embed(
            title="Training Certification Status",
            description=f"Training certification request for **{self.certification}** has been **accepted** by **{interaction.user.display_name}**.",
            color=Colour.green(),
            timestamp=datetime.now(timezone.utc)
        )
        status_embed.add_field(name="Link to Request", value=f"[Jump to request]({self.original_message.jump_url})", inline=False)
        status_embed.set_footer(text=f"Issued by {interaction.user.display_name}")

        try:
            await self.original_message.edit(embed=embed, view=None)
            await channel.send(content=self.user.mention, embed=status_embed)
            await interaction.response.send_message(f"Training certification request for {self.certification} accepted!", ephemeral=True)
            logger.info(f"Training certification {self.certification} accepted for {self.user} by {interaction.user}")
        except Exception as e:
            logger.error(f"Failed to process accept action: {str(e)}", exc_info=True)
            await interaction.response.send_message(f"Error processing accept: {str(e)}", ephemeral=True)
        self.stop()

    @discord.ui.button(label="Deny", style=ButtonStyle.red)
    async def deny_button(self, interaction: Interaction, button: Button):
        channel = interaction.client.get_channel(CONFIG["STATUS_CHANNEL_ID"])
        if not channel:
            logger.error(f"Target channel {CONFIG['STATUS_CHANNEL_ID']} not found")
            await interaction.response.send_message("Error: Status channel not found.", ephemeral=True)
            return

        self.history.append(f"❌ Denied by {interaction.user.display_name} at {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
        embed = Embed(
            title="Certification Training Request",
            description="**Status: Denied ❌**",
            color=Colour.red(),
            timestamp=datetime.now(timezone.utc)
        )
        embed.add_field(name="User", value=f"{self.user.mention} ({self.user.id})", inline=False)
        embed.add_field(name="Training Certification", value=self.certification, inline=False)
        embed.add_field(name="When", value=self.original_message.embeds[0].fields[2].value, inline=False)
        embed.add_field(name="Status History", value="\n".join(self.history), inline=False)
        embed.set_thumbnail(url=CONFIG["THUMBNAIL_URL"])
        embed.set_footer(text=f"Requested by {self.user.display_name}")

        status_embed = Embed(
            title="Training Certification Status",
            description=f"Training certification request for **{self.certification}** has been **denied** by **{interaction.user.display_name}**.",
            color=Colour.red(),
            timestamp=datetime.now(timezone.utc)
        )
        status_embed.add_field(name="Link to Request", value=f"[Jump to request]({self.original_message.jump_url})", inline=False)
        status_embed.set_footer(text=f"Issued by {interaction.user.display_name}")

        try:
            await self.original_message.edit(embed=embed, view=None)
            await channel.send(content=self.user.mention, embed=status_embed)
            await interaction.response.send_message(f"Training certification request for {self.certification} denied!", ephemeral=True)
            logger.info(f"Training certification {self.certification} denied for {self.user} by {interaction.user}")
        except Exception as e:
            logger.error(f"Failed to process deny action: {str(e)}", exc_info=True)
            await interaction.response.send_message(f"Error processing deny: {str(e)}", ephemeral=True)
        self.stop()

class TrainingCertRequestView(View):
    def __init__(self, user: Member, when: str, existing_requests: set):
        super().__init__(timeout=60)
        self.user = user
        self.when = when
        self.existing_requests = existing_requests

    @discord.ui.select(
        placeholder="Select a Training Certification",
        options=[
            discord.SelectOption(label="Grappler", value="Grappler", emoji="🧰"),
            discord.SelectOption(label="Undercover", value="Undercover", emoji="🕵️"),
            discord.SelectOption(label="Spike-Strip", value="Spike-Strip", emoji="🚧"),
            discord.SelectOption(label="Negotiator", value="Negotiator", emoji="🤝"),
            discord.SelectOption(label="Sniper", value="Sniper", emoji="🎯"),
            discord.SelectOption(label="G36C", value="G36C", emoji="🔫"),
            discord.SelectOption(label="Bearcat", value="Bearcat", emoji="🚓"),
        ]
    )
    async def select_callback(self, interaction: Interaction, select: Select):
        if interaction.user != self.user:
            await interaction.response.send_message("🚫 Only the user who initiated the request can select a certification!", ephemeral=True)
            logger.info(f"Unauthorized select attempt by {interaction.user} for {self.user}'s request")
            return

        selected_cert = select.values[0]
        if selected_cert in self.existing_requests:
            await interaction.response.send_message(f"🚫 You already have a pending or accepted request for **{selected_cert}**. Please wait until it is resolved or request a different certification.", ephemeral=True)
            logger.info(f"Duplicate certification request for {selected_cert} by {self.user} in guild {interaction.guild.id}")
            return

        channel = interaction.client.get_channel(CONFIG["REQUEST_CHANNEL_ID"])
        if not channel:
            logger.error(f"Target channel {CONFIG['REQUEST_CHANNEL_ID']} not found")
            await interaction.response.send_message("Error: Request channel not found.", ephemeral=True)
            return

        request_embed = Embed(
            title="Certification Training Request",
            description="**Status: Pending ⏳**",
            color=Colour.blue(),
            timestamp=datetime.now(timezone.utc)
        )
        request_embed.add_field(name="User", value=f"{self.user.mention} ({self.user.id})", inline=False)
        request_embed.add_field(name="Training Certification", value=selected_cert, inline=False)
        request_embed.add_field(name="When", value=self.when, inline=False)
        request_embed.add_field(name="Status History", value=f"📝 Submitted by {self.user.display_name} at {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}", inline=False)
        request_embed.set_thumbnail(url=CONFIG["THUMBNAIL_URL"])
        request_embed.set_footer(text=f"Requested by {self.user.display_name}")

        confirmation_embed = Embed(
            title="✅ Training Certification Request Submitted",
            description=f"Your training certification request for **{selected_cert}** has been sent to {channel.mention}!",
            color=Colour.from_rgb(46, 204, 113), 
            timestamp=datetime.now(timezone.utc)
        )
        confirmation_embed.add_field(name="Training Certification", value=selected_cert, inline=False)
        confirmation_embed.add_field(name="When", value=self.when, inline=False)
        confirmation_embed.set_footer(text=f"Requested by {self.user.display_name}")

        try:
            view = TrainingCertActionView(
                user=self.user,
                certification=selected_cert,
                original_message=None,
                history=[f"📝 Submitted by {self.user.display_name} at {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}"]
            )
            message = await channel.send(content=f"<@&{FTO_ROLE_ID}>", embed=request_embed, view=view)
            view.original_message = message
            await message.edit(view=view)

            await interaction.response.send_message(embed=confirmation_embed, ephemeral=True)
            logger.info(f"Training certification request for {selected_cert} sent by {self.user} to channel {CONFIG['REQUEST_CHANNEL_ID']}")
        except Exception as e:
            logger.error(f"Failed to send training certification request embed: {str(e)}", exc_info=True)
            await interaction.response.send_message(f"Error sending training certification request: {str(e)}", ephemeral=True)
        self.stop()

class CertsRequests(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.active_requests = {}  # Store active requests per user
        logger.info("CertificationTrainingRequests cog initialized")

    async def cog_load(self):
        logger.info("CertificationTrainingRequests cog loaded")
        for guild_id in CONFIG["GUILD_IDS"]:
            try:
                synced = await self.bot.tree.sync(guild=discord.Object(id=guild_id))
                logger.info(f"Synced {len(synced)} commands for guild {guild_id}")
            except Exception as e:
                logger.error(f"Failed to sync commands for guild {guild_id}: {str(e)}", exc_info=True)

    async def cog_command_error(self, ctx: commands.Context, error: commands.CommandError):
        logger.error(f"Command error in {ctx.command}: {str(error)}", exc_info=True)
        await ctx.send(f"❌ Error: {str(error)}", ephemeral=True)

    @commands.hybrid_command(
        name="requestcerts",
        description="Request a training certification with a specified time."
    )
    @app_commands.describe(time="Time for the training certification request (e.g., '1d', '2025-06-15')")
    @commands.cooldown(1, 60, commands.BucketType.user)
    async def requestcerts(self, ctx: commands.Context, time: str):
        try:
            if not ctx.guild:
                await ctx.send("🚫 This command can only be used in a server.", ephemeral=True)
                logger.error(f"requestcerts command attempted in DM by {ctx.author}")
                return

            if CONFIG["ALLOWED_ROLE_ID"]:
                role = ctx.guild.get_role(CONFIG["ALLOWED_ROLE_ID"])
                if not role or role not in ctx.author.roles:
                    await ctx.send("🚫 You don't have permission to use this command.", ephemeral=True)
                    logger.info(f"Unauthorized requestcerts attempt by {ctx.author} in guild {ctx.guild.id}")
                    return

            if not time or len(time) > 50:
                await ctx.send("🚫 Invalid time format. Please provide a valid time (e.g., '1d', '2025-06-15').", ephemeral=True)
                logger.info(f"Invalid time input '{time}' by {ctx.author} in guild {ctx.guild.id}")
                return

            existing_requests = self.active_requests.get(ctx.author.id, set())
            view = TrainingCertRequestView(user=ctx.author, when=time, existing_requests=existing_requests)
            await ctx.send("📋 Please select a training certification from the dropdown below:", view=view, delete_after=60)
            logger.info(f"requestcerts command executed by {ctx.author} in guild {ctx.guild.id} with time: {time}")
        except Exception as e:
            logger.error(f"requestcerts command failed for {ctx.author} in guild {ctx.guild.id}: {str(e)}", exc_info=True)
            await ctx.send(f"❌ Error executing command: {str(e)}", ephemeral=True)

    @commands.hybrid_command(
        name="listcerts",
        description="List available training certifications."
    )
    async def listcerts(self, ctx: commands.Context):
        try:
            embed = Embed(
                title="📜 Available Training Certifications",
                description="List of training certifications you can request with `!requestcerts` or `/requestcerts`.",
                color=Colour.blue(),
                timestamp=datetime.now(timezone.utc)
            )
            certs = [
                "🧰 Grappler",
                "🕵️ Undercover",
                "🚧 Spike-Strip",
                "🤝 Negotiator",
                "🎯 Sniper",
                "🔫 G36C",
                "🚓 Bearcat"
            ]
            embed.add_field(name="Training Certifications", value="\n".join(certs), inline=False)
            embed.set_footer(text=f"Requested by {ctx.author.display_name}")
            await ctx.send(embed=embed, ephemeral=True)
            logger.info(f"listcerts command executed by {ctx.author} in guild {ctx.guild.id}")
        except Exception as e:
            logger.error(f"listcerts command failed for {ctx.author} in guild {ctx.guild.id}: {str(e)}", exc_info=True)
            await ctx.send(f"❌ Error executing command: {str(e)}", ephemeral=True)

    @commands.hybrid_command(
        name="setbot",
        description="Set the bot's status and activity. Use quotes for multi-word activity (e.g., \"Under Maintenance\")."
    )
    @app_commands.describe(
        status="The status to set: dnd, online, offline, or idle",
        activity="The activity to display (e.g., 'Training Requests' or leave empty to clear)"
    )
    @app_commands.choices(status=[
        app_commands.Choice(name="Do Not Disturb", value="dnd"),
        app_commands.Choice(name="Online", value="online"),
        app_commands.Choice(name="Offline", value="offline"),
        app_commands.Choice(name="Idle", value="idle")
    ])
    @commands.has_permissions(administrator=True)
    async def setbot(self, ctx: commands.Context, status: str, *, activity: str = ""):
        try:
            if not ctx.guild:
                await ctx.send("🚫 This command can only be used in a server.", ephemeral=True)
                logger.error(f"setbot command attempted in DM by {ctx.author}")
                return

            status_map = {
                "dnd": Status.dnd,
                "online": Status.online,
                "offline": Status.offline,
                "idle": Status.idle
            }

            if status.lower() not in status_map:
                await ctx.send("🚫 Invalid status. Please use one of: dnd, online, offline, idle.", ephemeral=True)
                logger.info(f"Invalid status input '{status}' by {ctx.author} in guild {ctx.guild.id}")
                return

            if len(activity) > 100:
                await ctx.send("🚫 Activity must be 100 characters or less.", ephemeral=True)
                logger.info(f"Invalid activity length '{len(activity)}' by {ctx.author} in guild {ctx.guild.id}")
                return

            discord_status = status_map[status.lower()]
            activity_obj = Activity(type=ActivityType.watching, name=activity) if activity else None

            await self.bot.change_presence(status=discord_status, activity=activity_obj)
            activity_display = activity if activity else "none"
            embed = Embed(
                title="✅ Bot Presence Updated",
                description=f"Bot status set to **{status.lower()}** with activity **Watching {activity_display}**.",
                color=Colour.green(),
                timestamp=datetime.now(timezone.utc)
            )
            embed.set_footer(text=f"Updated by {ctx.author.display_name}")
            await ctx.send(embed=embed, ephemeral=True)
            logger.info(f"Bot presence set to status '{status.lower()}' and activity 'Watching {activity_display}' by {ctx.author} in guild {ctx.guild.id}")
        except Exception as e:
            logger.error(f"setbot command failed for {ctx.author} in guild {ctx.guild.id}: {str(e)}", exc_info=True)
            await ctx.send(f"❌ Error setting bot presence: {str(e)}", ephemeral=True)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.channel.id != CONFIG["REQUEST_CHANNEL_ID"]:
            return
        if message.author.bot:
            return
        if message.embeds and message.embeds[0].title == "Certification Training Request":
            user_id = int(message.embeds[0].fields[0].value.split('(')[1].split(')')[0])
            certification = message.embeds[0].fields[1].value
            status = message.embeds[0].description.split('**Status: ')[1].split('**')[0]
            if status in ["Pending ⏳", "Accepted ✅"]:
                self.active_requests.setdefault(user_id, set()).add(certification)
            elif status == "Denied ❌":
                self.active_requests.get(user_id, set()).discard(certification)
                if not self.active_requests.get(user_id):
                    self.active_requests.pop(user_id, None)

    @requestcerts.error
    async def requestcerts_error(self, ctx: commands.Context, error: commands.CommandError):
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.send(f"⏰ Please wait {error.retry_after:.1f} seconds before using this command again.", ephemeral=True)
            logger.info(f"Cooldown triggered for {ctx.author} in guild {ctx.guild.id}: {error.retry_after:.1f} seconds")
        else:
            await self.cog_command_error(ctx, error)

    @setbot.error
    async def setbot_error(self, ctx: commands.Context, error: commands.CommandError):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("🚫 You need administrator permissions to use this command.", ephemeral=True)
            logger.info(f"Missing permissions for setbot by {ctx.author} in guild {ctx.guild.id}")
        else:
            await self.cog_command_error(ctx, error)

async def setup(bot):
    await bot.add_cog(CertsRequests(bot))
    logger.info("CertificationTrainingRequests cog added to bot")
