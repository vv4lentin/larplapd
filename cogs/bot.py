import discord
from discord.ext import commands
import logging
from datetime import datetime
import time
import psutil
import asyncio
import sys
import re

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('CMD')

# Define the allowed user ID
ALLOWED_USER_ID = 1038522974988411000

class Bot(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.start_time = time.time()
        self.maintenance_mode = False
        self.shutdown_initiated = False
        logger.info("CMD cog initialized")

    # Helper to check if command is from allowed user
    async def cog_check(self, ctx):
        if ctx.author.id != ALLOWED_USER_ID:
            await ctx.send("This bot can only be used by the designated user.", ephemeral=True)
            return False
        return True

    # Helper to format uptime
    def format_uptime(self):
        uptime_seconds = int(time.time() - self.start_time)
        days, remainder = divmod(uptime_seconds, 86400)
        hours, remainder = divmod(remainder, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{days}d {hours}h {minutes}m {seconds}s"

    # Helper to get latency color
    def get_latency_color(self, latency_ms):
        try:
            if latency_ms < 100:
                return discord.Color.green()
            elif latency_ms < 200:
                return discord.Color.gold()
            else:
                return discord.Color.red()
        except Exception as e:
            logger.error(f"Latency color error: {e}")
            return discord.Color.blue()

    # Helper to get system resources
    def get_system_resources(self):
        try:
            cpu_percent = psutil.cpu_percent()
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            return {
                'cpu': f"{cpu_percent}%",
                'memory': f"{memory.percent}% ({memory.used / 1024**3:.2f}/{memory.total / 1024**3:.2f} GB)",
                'disk': f"{disk.percent}% ({disk.used / 1024**3:.2f}/{disk.total / 1024**3:.2f} GB)"
            }
        except Exception as e:
            logger.error(f"System resources error: {e}")
            return {'cpu': 'N/A', 'memory': 'N/A', 'disk': 'N/A'}

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CommandNotFound):
            command_name = ctx.message.content.split()[0][len(ctx.prefix):]
            await ctx.send(f"`{command_name}` is not a command. Use `,help` to see available commands.", ephemeral=True)
        elif isinstance(error, commands.CheckFailure):
            return  # Handled by cog_check
        else:
            logger.error(f"Command error in {ctx.guild.id if ctx.guild else 'DM'}: {error}")
            await ctx.send(f"An error occurred: {str(error)}", ephemeral=True)

    @commands.command(name='purge')
    @commands.has_permissions(manage_messages=True)
    @commands.bot_has_permissions(manage_messages=True)
    async def purge(self, ctx, amount: int):
        logger.info(f"Purge command invoked by {ctx.author} for {amount} messages")
        if amount < 1 or amount > 100:
            await ctx.send("Please specify a number between 1 and 100.", ephemeral=True)
            return
        await ctx.channel.purge(limit=amount + 1)
        await ctx.send(f"Successfully deleted {amount} message(s).", delete_after=5)

    @purge.error
    async def purge_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("You need 'Manage Messages' permission.", ephemeral=True)
        elif isinstance(error, commands.BotMissingPermissions):
            await ctx.send("I need 'Manage Messages' permission.", ephemeral=True)
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("Please specify the number of messages to purge.", ephemeral=True)
        elif isinstance(error, commands.CheckFailure):
            return  # Handled by cog_check
        else:
            logger.error(f"Purge error: {error}")
            await ctx.send(f"Error: {str(error)}", ephemeral=True)

    @commands.command(name='checkperms')
    async def checkperms(self, ctx, member: discord.Member = None):
        logger.info(f"Checkperms command invoked by {ctx.author} for {member or ctx.author}")
        member = member or ctx.author
        perms = member.guild_permissions
        perm_list = [f"{perm} = {value}" for perm, value in perms if value]
        if not perm_list:
            await ctx.send(f"{member.mention} has no notable permissions.", ephemeral=True)
            return
        embed = discord.Embed(title=f"Permissions for {member.display_name}", description="\n".join(perm_list), color=discord.Color.blue())
        await ctx.send(embed=embed, ephemeral=True)

    @checkperms.error
    async def checkperms_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("You need 'Manage Roles' permission.", ephemeral=True)
        elif isinstance(error, commands.CheckFailure):
            return  # Handled by cog_check
        else:
            logger.error(f"Checkperms error: {error}")
            await ctx.send(f"Error: {str(error)}", ephemeral=True)

    class ActivityModal(discord.ui.Modal, title="Change Bot Activity"):
        def __init__(self, cog):
            super().__init__()
            self.cog = cog
            self.activity_name = discord.ui.TextInput(
                label="Activity Name",
                placeholder="e.g., Playing a game",
                max_length=128,
                required=True
            )
            self.activity_type = discord.ui.Select(
                placeholder="Select Activity Type",
                min_values=1,
                max_values=1,
                options=[
                    discord.SelectOption(label="Playing", value="playing", emoji="🎮"),
                    discord.SelectOption(label="Streaming", value="streaming", emoji="📹"),
                    discord.SelectOption(label="Listening", value="listening", emoji="🎧"),
                    discord.SelectOption(label="Watching", value="watching", emoji="📺")
                ]
            )
            self.activity_url = discord.ui.TextInput(
                label="Stream URL (Optional, for Streaming)",
                placeholder="e.g., https://twitch.tv/username",
                max_length=256,
                required=False
            )
            self.temporary = discord.ui.Select(
                placeholder="Temporary Activity?",
                min_values=1,
                max_values=1,
                options=[
                    discord.SelectOption(label="Permanent", value="permanent"),
                    discord.SelectOption(label="Temporary (5 min)", value="temporary")
                ]
            )
            self.add_item(self.activity_name)
            self.add_item(self.activity_type)
            self.add_item(self.activity_url)
            self.add_item(self.temporary)

        async def on_submit(self, interaction: discord.Interaction):
            if interaction.user.id != ALLOWED_USER_ID:
                await interaction.response.send_message("This feature is only available to the designated user.", ephemeral=True)
                return

            try:
                activity_type = self.activity_type.values[0]
                name = self.activity_name.value.strip()
                url = self.activity_url.value.strip() if self.activity_url.value else None
                is_temporary = self.temporary.values[0] == "temporary"

                if not name:
                    await interaction.response.send_message("Activity name cannot be empty.", ephemeral=True)
                    return

                if activity_type == "streaming" and url:
                    twitch_pattern = r'^https?://(www\.)?twitch\.tv/[\w]+$'
                    youtube_pattern = r'^https?://(www\.)?youtube\.com/watch\?v=[\w-]+$'
                    if not (re.match(twitch_pattern, url) or re.match(youtube_pattern, url)):
                        await interaction.response.send_message("Streaming URL must be a valid Twitch or YouTube URL.", ephemeral=True)
                        return

                activity = None
                if activity_type == "playing":
                    activity = discord.Game(name=name)
                elif activity_type == "streaming":
                    activity = discord.Streaming(name=name, url=url if url else None)
                elif activity_type == "listening":
                    activity = discord.Activity(type=discord.ActivityType.listening, name=name)
                elif activity_type == "watching":
                    activity = discord.Activity(type=discord.ActivityType.watching, name=name)

                if activity is None:
                    await interaction.response.send_message("Invalid activity type.", ephemeral=True)
                    return

                await interaction.client.change_presence(activity=activity)
                response = f"Bot activity set to: {activity_type.capitalize()} {name}" + (f" ({url})" if url else "") + (" (temporary for 5 min)" if is_temporary else "")
                await interaction.response.send_message(response, ephemeral=True)

                if is_temporary:
                    await asyncio.sleep(300)
                    await interaction.client.change_presence(activity=None)

            except Exception as e:
                logger.error(f"ActivityModal submission error: {e}")
                await interaction.response.send_message(f"Failed to change activity: {str(e)}", ephemeral=True)

        async def on_error(self, interaction: discord.Interaction, error: Exception):
            logger.error(f"ActivityModal error: {error}")
            await interaction.response.send_message("An error occurred while processing the modal.", ephemeral=True)

    class ActivityTypeModal(discord.ui.Modal, title="Change Activity Type"):
        def __init__(self, cog, current_activity):
            super().__init__()
            self.cog = cog
            self.current_activity = current_activity
            self.activity_type = discord.ui.Select(
                placeholder="Select New Activity Type",
                min_values=1,
                max_values=1,
                options=[
                    discord.SelectOption(label="Playing", value="playing", emoji="🎮"),
                    discord.SelectOption(label="Streaming", value="streaming", emoji="📹"),
                    discord.SelectOption(label="Listening", value="listening", emoji="🎧"),
                    discord.SelectOption(label="Watching", value="watching", emoji="📺")
                ]
            )
            self.activity_url = discord.ui.TextInput(
                label="Stream URL (Optional, for Streaming)",
                placeholder="e.g., https://twitch.tv/username",
                max_length=256,
                required=False
            )
            self.temporary = discord.ui.Select(
                placeholder="Temporary Activity?",
                min_values=1,
                max_values=1,
                options=[
                    discord.SelectOption(label="Permanent", value="permanent"),
                    discord.SelectOption(label="Temporary (5 min)", value="temporary")
                ]
            )
            self.add_item(self.activity_type)
            self.add_item(self.activity_url)
            self.add_item(self.temporary)

        async def on_submit(self, interaction: discord.Interaction):
            if interaction.user.id != ALLOWED_USER_ID:
                await interaction.response.send_message("This feature is only available to the designated user.", ephemeral=True)
                return

            try:
                activity_type = self.activity_type.values[0]
                name = self.current_activity.name if self.current_activity else "Default"
                url = self.activity_url.value.strip() if self.activity_url.value else None
                is_temporary = self.temporary.values[0] == "temporary"

                if activity_type == "streaming" and url:
                    twitch_pattern = r'^https?://(www\.)?twitch\.tv/[\w]+$'
                    youtube_pattern = r'^https?://(www\.)?youtube\.com/watch\?v=[\w-]+$'
                    if not (re.match(twitch_pattern, url) or re.match(youtube_pattern, url)):
                        await interaction.response.send_message("Streaming URL must be a valid Twitch or YouTube URL.", ephemeral=True)
                        return

                activity = None
                if activity_type == "playing":
                    activity = discord.Game(name=name)
                elif activity_type == "streaming":
                    activity = discord.Streaming(name=name, url=url if url else None)
                elif activity_type == "listening":
                    activity = discord.Activity(type=discord.ActivityType.listening, name=name)
                elif activity_type == "watching":
                    activity = discord.Activity(type=discord.ActivityType.watching, name=name)

                if activity is None:
                    await interaction.response.send_message("Invalid activity type.", ephemeral=True)
                    return

                await interaction.client.change_presence(activity=activity)
                response = f"Bot activity type changed to: {activity_type.capitalize()} {name}" + (f" ({url})" if url else "") + (" (temporary for 5 min)" if is_temporary else "")
                await interaction.response.send_message(response, ephemeral=True)

                if is_temporary:
                    await asyncio.sleep(300)
                    await interaction.client.change_presence(activity=None)

            except Exception as e:
                logger.error(f"ActivityTypeModal submission error: {e}")
                await interaction.response.send_message(f"Failed to change activity type: {str(e)}", ephemeral=True)

        async def on_error(self, interaction: discord.Interaction, error: Exception):
            logger.error(f"ActivityTypeModal error: {error}")
            await interaction.response.send_message("An error occurred while processing the modal.", ephemeral=True)

    class AnnouncementModal(discord.ui.Modal, title="Send Announcement"):
        def __init__(self, cog):
            super().__init__()
            self.cog = cog
            self.channel_id = discord.ui.TextInput(
                label="Channel ID (or 'all' for all guilds)",
                placeholder="e.g., 123456789012345678 or 'all'",
                max_length=20,
                required=True
            )
            self.message = discord.ui.TextInput(
                label="Announcement Message",
                placeholder="Enter the message to send",
                style=discord.TextStyle.paragraph,
                max_length=2000,
                required=True
            )
            self.add_item(self.channel_id)
            self.add_item(self.message)

        async def on_submit(self, interaction: discord.Interaction):
            if interaction.user.id != ALLOWED_USER_ID:
                await interaction.response.send_message("This feature is only available to the designated user.", ephemeral=True)
                return

            channel_id = self.channel_id.value
            message = self.message.value

            try:
                if channel_id.lower() == "all":
                    sent_count = 0
                    for guild in interaction.client.guilds:
                        channel = guild.system_channel
                        if channel and channel.permissions_for(guild.me).send_messages:
                            try:
                                await channel.send(message)
                                sent_count += 1
                                await asyncio.sleep(1)
                            except Exception as e:
                                logger.warning(f"Failed to send announcement to {guild.id}: {e}")
                    await interaction.response.send_message(f"Announcement sent to {sent_count} guild(s).", ephemeral=True)
                else:
                    try:
                        channel = interaction.client.get_channel(int(channel_id))
                        if not channel:
                            await interaction.response.send_message("Invalid channel ID.", ephemeral=True)
                            return
                        if not channel.permissions_for(interaction.guild.me).send_messages:
                            await interaction.response.send_message("I lack permission to send messages in that channel.", ephemeral=True)
                            return
                        await channel.send(message)
                        await interaction.response.send_message(f"Announcement sent to <#{channel_id}>.", ephemeral=True)
                    except ValueError:
                        await interaction.response.send_message("Channel ID must be a number or 'all'.", ephemeral=True)
            except Exception as e:
                logger.error(f"Announcement error: {e}")
                await interaction.response.send_message(f"Failed to send announcement: {str(e)}", ephemeral=True)

        async def on_error(self, interaction: discord.Interaction, error: Exception):
            logger.error(f"AnnouncementModal error: {error}")
            await interaction.response.send_message("An error occurred while processing the modal.", ephemeral=True)

    class BotPanelView(discord.ui.View):
        def __init__(self, cog):
            super().__init__(timeout=None)
            self.cog = cog

        async def interaction_check(self, interaction: discord.Interaction) -> bool:
            if interaction.user.id != ALLOWED_USER_ID:
                await interaction.response.send_message("This panel is only available to the designated user.", ephemeral=True)
                return False
            return True

        @discord.ui.button(label="Change Activity", style=discord.ButtonStyle.primary, emoji="✨", row=0)
        async def change_activity(self, interaction: discord.Interaction, button: discord.ui.Button):
            try:
                modal = self.cog.ActivityModal(self.cog)
                await interaction.response.send_modal(modal)
            except Exception as e:
                logger.error(f"Change Activity button error: {e}")
                await interaction.response.send_message("Failed to open activity modal.", ephemeral=True)

        @discord.ui.button(label="Change Activity Type", style=discord.ButtonStyle.primary, emoji="🔄", row=0)
        async def change_activity_type(self, interaction: discord.Interaction, button: discord.ui.Button):
            try:
                current_activity = interaction.client.activity
                modal = self.cog.ActivityTypeModal(self.cog, current_activity)
                await interaction.response.send_modal(modal)
            except Exception as e:
                logger.error(f"Change Activity Type button error: {e}")
                await interaction.response.send_message("Failed to open activity type modal.", ephemeral=True)

        @discord.ui.button(label="Restart Activity", style=discord.ButtonStyle.secondary, emoji="🔃", row=0)
        async def restart_activity(self, interaction: discord.Interaction, button: discord.ui.Button):
            current_activity = interaction.client.activity
            if not current_activity:
                await interaction.response.send_message("No activity is currently set.", ephemeral=True)
                return
            try:
                await interaction.client.change_presence(activity=current_activity)
                await interaction.response.send_message(f"Bot activity restarted: {current_activity.name}", ephemeral=True)
            except Exception as e:
                logger.error(f"Restart activity error: {e}")
                await interaction.response.send_message(f"Failed to restart activity: {str(e)}", ephemeral=True)

        @discord.ui.button(label="Stop Activity", style=discord.ButtonStyle.red, emoji="🛑", row=0)
        async def stop_activity(self, interaction: discord.Interaction, button: discord.ui.Button):
            try:
                await interaction.client.change_presence(activity=None)
                await interaction.response.send_message("Bot activity cleared.", ephemeral=True)
            except Exception as e:
                logger.error(f"Stop activity error: {e}")
                await interaction.response.send_message(f"Failed to clear activity: {str(e)}", ephemeral=True)

        @discord.ui.button(label="Set Online", style=discord.ButtonStyle.green, emoji="🟢", row=1)
        async def set_online(self, interaction: discord.Interaction, button: discord.ui.Button):
            try:
                await interaction.client.change_presence(status=discord.Status.online)
                await interaction.response.send_message("Bot status set to Online.", ephemeral=True)
            except Exception as e:
                logger.error(f"Set online error: {e}")
                await interaction.response.send_message(f"Failed to set Online status: {str(e)}", ephemeral=True)

        @discord.ui.button(label="Set Idle", style=discord.ButtonStyle.secondary, emoji="🟡", row=1)
        async def set_idle(self, interaction: discord.Interaction, button: discord.ui.Button):
            try:
                await interaction.client.change_presence(status=discord.Status.idle)
                await interaction.response.send_message("Bot status set to Idle.", ephemeral=True)
            except Exception as e:
                logger.error(f"Set idle error: {e}")
                await interaction.response.send_message(f"Failed to set Idle status: {str(e)}", ephemeral=True)

        @discord.ui.button(label="Set DND", style=discord.ButtonStyle.danger, emoji="🔴", row=1)
        async def set_dnd(self, interaction: discord.Interaction, button: discord.ui.Button):
            try:
                await interaction.client.change_presence(status=discord.Status.dnd)
                await interaction.response.send_message("Bot status set to Do Not Disturb.", ephemeral=True)
            except Exception as e:
                logger.error(f"Set DND error: {e}")
                await interaction.response.send_message(f"Failed to set DND status: {str(e)}", ephemeral=True)

        @discord.ui.button(label="Toggle Invisible", style=discord.ButtonStyle.grey, emoji="👻", row=1)
        async def toggle_invisible(self, interaction: discord.Interaction, button: discord.ui.Button):
            current_status = interaction.client.status
            new_status = discord.Status.invisible if current_status != discord.Status.invisible else discord.Status.online
            try:
                await interaction.client.change_presence(status=new_status)
                status_text = "Invisible" if new_status == discord.Status.invisible else "Online"
                await interaction.response.send_message(f"Bot status set to {status_text}.", ephemeral=True)
            except Exception as e:
                logger.error(f"Toggle invisible error: {e}")
                await interaction.response.send_message(f"Failed to toggle status: {str(e)}", ephemeral=True)

        @discord.ui.button(label="Toggle Maintenance", style=discord.ButtonStyle.grey, emoji="🛠️", row=2)
        async def toggle_maintenance(self, interaction: discord.Interaction, button: discord.ui.Button):
            self.cog.maintenance_mode = not self.cog.maintenance_mode
            try:
                if self.cog.maintenance_mode:
                    await interaction.client.change_presence(
                        status=discord.Status.dnd,
                        activity=discord.Activity(type=discord.ActivityType.watching, name="Under Maintenance")
                    )
                    await interaction.response.send_message("Maintenance mode enabled.", ephemeral=True)
                else:
                    await interaction.client.change_presence(status=discord.Status.online, activity=None)
                    await interaction.response.send_message("Maintenance mode disabled.", ephemeral=True)
            except Exception as e:
                logger.error(f"Maintenance toggle error: {e}")
                await interaction.response.send_message(f"Failed to toggle maintenance mode: {str(e)}", ephemeral=True)

        @discord.ui.button(label="Sync Globally", style=discord.ButtonStyle.blurple, emoji="🌐", row=2)
        async def sync_globally(self, interaction: discord.Interaction, button: discord.ui.Button):
            try:
                synced = await interaction.client.tree.sync()
                await interaction.response.send_message(f"Globally synced {len(synced)} command(s).", ephemeral=True)
            except Exception as e:
                logger.error(f"Global sync error: {e}")
                await interaction.response.send_message(f"Failed to sync globally: {str(e)}", ephemeral=True)

        @discord.ui.button(label="Shutdown Bot", style=discord.ButtonStyle.red, emoji="⏹️", row=2)
        async def shutdown_bot(self, interaction: discord.Interaction, button: discord.ui.Button):
            if self.cog.shutdown_initiated:
                await interaction.response.send_message("Shutdown already in progress.", ephemeral=True)
                return

            confirm_view = discord.ui.View(timeout=30)
            confirm_button = discord.ui.Button(label="Confirm Shutdown", style=discord.ButtonStyle.danger)
            cancel_button = discord.ui.Button(label="Cancel", style=discord.ButtonStyle.secondary)

            async def confirm_callback(interaction: discord.Interaction):
                self.cog.shutdown_initiated = True
                try:
                    await interaction.response.edit_message(content="Shutting down bot...", view=None)
                    await interaction.client.change_presence(status=discord.Status.offline)
                    await interaction.client.close()
                    sys.exit(0)
                except Exception as e:
                    self.cog.shutdown_initiated = False
                    logger.error(f"Shutdown error: {e}")
                    await interaction.followup.send(f"Failed to shutdown bot: {str(e)}", ephemeral=True)

            async def cancel_callback(interaction: discord.Interaction):
                await interaction.response.edit_message(content="Shutdown cancelled.", view=None)

            confirm_button.callback = confirm_callback
            cancel_button.callback = cancel_callback
            confirm_view.add_item(confirm_button)
            confirm_view.add_item(cancel_button)

            await interaction.response.send_message("Are you sure you want to shut down the bot?", view=confirm_view, ephemeral=True)

        @discord.ui.button(label="Send Announcement", style=discord.ButtonStyle.blurple, emoji="📢", row=2)
        async def send_announcement(self, interaction: discord.Interaction, button: discord.ui.Button):
            try:
                modal = self.cog.AnnouncementModal(self.cog)
                await interaction.response.send_modal(modal)
            except Exception as e:
                logger.error(f"Send Announcement error: {e}")
                await interaction.response.send_message("Failed to open announcement modal.", ephemeral=True)

        @discord.ui.button(label="Check Bot Perms", style=discord.ButtonStyle.secondary, emoji="🔍", row=3)
        async def check_bot_perms(self, interaction: discord.Interaction, button: discord.ui.Button):
            try:
                bot_member = interaction.guild.me
                perms = bot_member.guild_permissions
                perm_list = [f"{perm} = {value}" for perm, value in perms if value]
                embed = discord.Embed(title=f"Bot Permissions: {interaction.client.user.name}", color=discord.Color.green())
                embed.add_field(name="Permissions", value="\n".join(perm_list) or "None", inline=False)
                await interaction.response.send_message(embed=embed, ephemeral=True)
            except Exception as e:
                logger.error(f"Check bot perms error: {e}")
                await interaction.response.send_message(f"Failed to check permissions: {str(e)}", ephemeral=True)

        @discord.ui.button(label="Resource Usage", style=discord.ButtonStyle.secondary, emoji="📊", row=3)
        async def resource_usage(self, interaction: discord.Interaction, button: discord.ui.Button):
            try:
                resources = self.cog.get_system_resources()
                embed = discord.Embed(title="System Resource Usage", color=discord.Color.blue())
                embed.add_field(name="CPU", value=resources['cpu'], inline=True)
                embed.add_field(name="Memory", value=resources['memory'], inline=True)
                embed.add_field(name="Disk", value=resources['disk'], inline=True)
                embed.set_footer(text=f"Requested by {interaction.user}")
                await interaction.response.send_message(embed=embed, ephemeral=True)
            except Exception as e:
                logger.error(f"Resource usage error: {e}")
                await interaction.response.send_message(f"Failed to check resource usage: {str(e)}", ephemeral=True)

        @discord.ui.button(label="Refresh Panel", style=discord.ButtonStyle.green, emoji="🔄", row=3)
        async def refresh_panel(self, interaction: discord.Interaction, button: discord.ui.Button):
            try:
                await interaction.response.defer(ephemeral=True)
                embed = discord.Embed(
                    title=f"{interaction.client.user.name} Control Panel",
                    description="Manage the bot's status, activity, and permissions using the buttons below.",
                    color=self.cog.get_latency_color(interaction.client.latency * 1000),
                    timestamp=datetime.now()
                )
                try:
                    embed.set_thumbnail(url=interaction.client.user.avatar.url if interaction.client.user.avatar else None)
                    embed.set_image(url=interaction.guild.icon.url if interaction.guild.icon else None)
                except Exception as e:
                    logger.warning(f"Embed image error: {e}")
                embed.add_field(name="Bot ID", value=interaction.client.user.id, inline=True)
                embed.add_field(name="Status", value=str(interaction.client.status).capitalize(), inline=True)
                embed.add_field(
                    name="Activity",
                    value=interaction.client.activity.name if interaction.client.activity else "None",
                    inline=True
                )
                embed.add_field(name="Latency", value=f"{interaction.client.latency * 1000:.2f} ms", inline=True)
                embed.add_field(name="Guilds", value=len(interaction.client.guilds), inline=True)
                embed.add_field(name="Uptime", value=self.cog.format_uptime(), inline=True)
                embed.set_footer(text=f"Requested by {interaction.user}")
                await interaction.edit_original_response(embed=embed, view=self)
            except Exception as e:
                logger.error(f"Refresh panel error: {e}")
                await interaction.response.send_message(f"Failed to refresh panel: {str(e)}", ephemeral=True)

    @commands.command(name='botpanel')
    async def botpanel(self, ctx):
        try:
            view = self.BotPanelView(self)
            embed = discord.Embed(
                title=f"{self.bot.user.name} Control Panel",
                description="Manage the bot's status, activity, and permissions using the buttons below.",
                color=self.get_latency_color(self.bot.latency * 1000),
                timestamp=datetime.now()
            )
            try:
                embed.set_thumbnail(url=self.bot.user.avatar.url if self.bot.user.avatar else None)
                embed.set_image(url=ctx.guild.icon.url if ctx.guild.icon else None)
            except Exception as e:
                logger.warning(f"Embed image error: {e}")
            embed.add_field(name="Bot ID", value=self.bot.user.id, inline=True)
            embed.add_field(name="Status", value=str(self.bot.status).capitalize(), inline=True)
            embed.add_field(
                name="Activity",
                value=self.bot.activity.name if self.bot.activity else "None",
                inline=True
            )
            embed.add_field(name="Latency", value=f"{self.bot.latency * 1000:.2f} ms", inline=True)
            embed.add_field(name="Guilds", value=len(self.bot.guilds), inline=True)
            embed.add_field(name="Uptime", value=self.format_uptime(), inline=True)
            embed.set_footer(text=f"Requested by {ctx.author}")
            await ctx.send(embed=embed, view=view, ephemeral=True)
        except Exception as e:
            logger.error(f"Botpanel error: {e}")
            await ctx.send(f"Failed to display bot panel: {str(e)}", ephemeral=True)

    @botpanel.error
    async def botpanel_error(self, ctx, error):
        if isinstance(error, commands.CheckFailure):
            return  # Handled by cog_check
        logger.error(f"Botpanel error: {error}")
        await ctx.send(f"Error: {str(error)}", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Bot(bot))
