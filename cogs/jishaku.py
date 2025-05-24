import discord
import asyncio
import subprocess
import textwrap
import io
import traceback
import datetime
import inspect
import os
import sys
import json
import shutil
from discord.ext import commands
from pathlib import Path
from discord.ui import Button, View
import logging

# Check discord.py version
if discord.__version__ not in ["2.3.2", "2.5.2"]:
    print(f"Warning: discord.py version {discord.__version__} detected. Jishaku tested with 2.3.2 and 2.5.2.")

# Configure logging with fallback
try:
    log_file = Path("bot.log")
    log_file.parent.mkdir(parents=True, exist_ok=True)
    if not os.access(log_file.parent, os.W_OK):
        raise PermissionError("No write permission for log directory")
    logging.basicConfig(
        filename=str(log_file),
        level=logging.INFO,
        format="%(asctime)s:%(levelname)s:%(name)s: %(message)s"
    )
except (PermissionError, OSError) as e:
    print(f"Logging to file failed: {e}. Falling back to console.")
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s:%(levelname)s:%(name)s: %(message)s",
        handlers=[logging.StreamHandler()]
    )
logger = logging.getLogger("Jishaku")

class PaginatorView(View):
    def __init__(self, paginator, author):
        super().__init__(timeout=60)
        self.paginator = paginator
        self.author = author
        self.message = None
        self.update_buttons()

    def update_buttons(self):
        self.prev_button.disabled = self.paginator.current_page == 0
        self.next_button.disabled = self.paginator.current_page >= len(self.paginator.pages) - 1

    async def on_timeout(self):
        if self.message:
            try:
                for item in self.children:
                    item.disabled = True
                await self.message.edit(view=self)
                logger.debug("Paginator view timed out")
            except discord.HTTPException as e:
                logger.warning(f"Failed to update paginator view on timeout: {e}")

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user != self.author:
            await interaction.response.send_message("Only the command author can use these buttons.", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="Previous", style=discord.ButtonStyle.blurple, emoji="⬅️")
    async def prev_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            self.paginator.prev_page()
            self.update_buttons()
            embed = discord.Embed(
                title=self.paginator.title,
                description=f"```py\n{self.paginator.get_page()}\n```",
                color=discord.Color.blue()
            )
            embed.set_footer(text=f"Page {self.paginator.current_page + 1}/{len(self.paginator.pages)}")
            await interaction.response.edit_message(embed=embed, view=self)
            logger.debug(f"{interaction.user} navigated to previous page")
        except discord.HTTPException as e:
            logger.error(f"Failed to update paginator (prev): {e}")
            await interaction.response.send_message("Failed to update page.", ephemeral=True)

    @discord.ui.button(label="Next", style=discord.ButtonStyle.blurple, emoji="➡️")
    async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            self.paginator.next_page()
            self.update_buttons()
            embed = discord.Embed(
                title=self.paginator.title,
                description=f"```py\n{self.paginator.get_page()}\n```",
                color=discord.Color.blue()
            )
            embed.set_footer(text=f"Page {self.paginator.current_page + 1}/{len(self.paginator.pages)}")
            await interaction.response.edit_message(embed=embed, view=self)
            logger.debug(f"{interaction.user} navigated to next page")
        except discord.HTTPException as e:
            logger.error(f"Failed to update paginator (next): {e}")
            await interaction.response.send_message("Failed to update page.", ephemeral=True)

class Paginator:
    def __init__(self, entries, title, per_page=10):
        self.entries = entries or ["No entries."]
        self.title = title
        self.per_page = per_page
        self.pages = [entries[i:i + per_page] for i in range(0, len(entries), per_page)]
        self.current_page = 0

    def get_page(self):
        return "\n".join(self.pages[self.current_page]) if self.pages else "No entries."

    def next_page(self):
        if self.current_page < len(self.pages) - 1:
            self.current_page += 1

    def prev_page(self):
        if self.current_page > 0:
            self.current_page -= 1

class Jishaku(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.start_time = datetime.datetime.utcnow()
        self.owner_ids = set()
        self.config = self._load_config()
        self.error_channel_id = self.config.get("error_channel_id")
        self._owners_fetched = False
        self._load_owners()
        logger.info("Jishaku cog initialized")

    def _load_config(self):
        config_path = Path("config.json")
        default_config = {
            "owner_ids": [],
            "error_channel_id": None,
            "max_log_lines": 100,
            "backup_dir": "backups"
        }
        try:
            if not config_path.exists():
                with config_path.open("w", encoding="utf-8") as f:
                    json.dump(default_config, f, indent=2)
                logger.info("Created default config.json")
                return default_config
            with config_path.open("r", encoding="utf-8") as f:
                config = json.load(f)
                return {**default_config, **config}
        except (json.JSONDecodeError, OSError, PermissionError) as e:
            logger.error(f"Failed to load config.json: {e}. Using defaults.")
            return default_config

    def _save_config(self):
        config_path = Path("config.json")
        try:
            with config_path.open("w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=2)
            logger.debug("Saved config.json")
        except (OSError, PermissionError) as e:
            logger.error(f"Failed to save config.json: {e}")

    def _load_owners(self):
        try:
            owner_ids = self.config.get("owner_ids", [])
            self.owner_ids = {int(oid) for oid in owner_ids if isinstance(oid, (int, str)) and str(oid).isdigit()}
            logger.info(f"Loaded owner IDs from config: {self.owner_ids}")
        except (ValueError, TypeError) as e:
            logger.error(f"Invalid owner_ids in config: {e}. Using empty set.")
            self.owner_ids = set()

    async def _fetch_owners(self):
        try:
            await self.bot.wait_until_ready()
            app_info = await self.bot.application_info()
            if app_info.team:
                self.owner_ids = {member.id for member in app_info.team.members}
            else:
                self.owner_ids = {app_info.owner.id}
            self.config["owner_ids"] = list(self.owner_ids)
            self._save_config()
            logger.info(f"Fetched owner IDs: {self.owner_ids}")
        except discord.HTTPException as e:
            logger.error(f"Failed to fetch owners: {e}")

    @commands.Cog.listener()
    async def on_ready(self):
        if not self._owners_fetched and not self.owner_ids:
            self._owners_fetched = True
            await self._fetch_owners()
            logger.info("Owner fetching completed in on_ready")

    async def cog_load(self):
        logger.info("Jishaku cog async initialization completed")

    async def cog_check(self, ctx):
        if not self.owner_ids:
            logger.warning("No owner IDs defined")
            await ctx.send("No bot owners configured.")
            return False
        if ctx.author.id not in self.owner_ids:
            logger.warning(f"{ctx.author} is not an owner")
            await ctx.send("This command is restricted to bot owners.")
            return False
        return True

    async def _send_paginated(self, ctx, entries, title, per_page=10):
        if not entries:
            await ctx.send(f"No {title.lower()} found.")
            return
        paginator = Paginator(entries, title, per_page)
        embed = discord.Embed(
            title=title,
            description=f"```py\n{paginator.get_page()}\n```",
            color=discord.Color.blue()
        )
        embed.set_footer(text=f"Page {paginator.current_page + 1}/{len(paginator.pages)}")
        try:
            view = PaginatorView(paginator, ctx.author)
            view.message = await ctx.send(embed=embed, view=view)
            logger.info(f"{ctx.author} received paginated output for {title}")
        except discord.Forbidden as e:
            logger.error(f"Failed to send paginated embed: {e}")
            await ctx.send("Failed to send embed. Ensure the bot has permissions to send messages and embed links.")
        except discord.HTTPException as e:
            logger.error(f"Failed to send paginated embed: {e}")
            await ctx.send(f"Failed to send embed: {str(e)}")

    async def _send_file(self, ctx, content, filename, max_length=2000):
        if len(content) <= max_length:
            try:
                await ctx.send(f"```{filename.split('.')[-1]}\n{content}\n```")
                logger.info(f"{ctx.author} received inline output: {filename}")
            except discord.Forbidden as e:
                logger.error(f"Failed to send inline message: {e}")
                await ctx.send("Failed to send message. Ensure the bot has permissions to send messages.")
            return
        file_path = Path(f"temp_{filename}")
        try:
            with file_path.open("w", encoding="utf-8") as f:
                f.write(content)
            if file_path.stat().st_size > 25 * 1024 * 1024:
                await ctx.send(f"Output too large to upload (>25MB). Saved to `{filename}`.")
            else:
                try:
                    await ctx.send(file=discord.File(file_path, filename))
                    logger.info(f"{ctx.author} received file output: {filename}")
                except discord.Forbidden as e:
                    logger.error(f"Failed to send file: {e}")
                    await ctx.send("Failed to send file. Ensure the bot has permissions to send files.")
                except discord.HTTPException as e:
                    logger.error(f"Failed to send file: {e}")
            await ctx.send(f"Failed to send file: {str(e)}")
        except OSError as e:
            logger.error(f"Failed to write file {filename}: {e}")
            await ctx.send(f"Failed to send file: {e}")
        finally:
            try:
                file_path.unlink(missing_ok=True)
            except OSError as e:
                logger.warning(f"Failed to delete temp file {file_path}: {e}")

    async def _report_error(self, ctx, error, command):
        if not self.error_channel_id:
            logger.debug("No error channel configured for error reporting")
            return
        channel = self.bot.get_channel(self.error_channel_id)
        if not channel:
            logger.warning(f"Error channel {self.error_channel_id} not found")
            return
        error_msg = f"Error in `{command}` by {ctx.author} ({ctx.author.id}):\n```py\n{str(error)}\n```"
        try:
            await channel.send(error_msg[:2000])
            logger.info(f"Reported error in {command} to error channel")
        except discord.HTTPException as e:
            logger.error(f"Failed to send error report: {e}")

    @commands.group(name="jishaku", aliases=["jsk"], invoke_without_command=True)
    async def jishaku(self, ctx):
        logger.info(f"{ctx.author} invoked jsk command")
        prefix = ctx.prefix
        commands_list = [
            f"- `{prefix}jsk_shutdown` - Shut down the bot.",
            f"- `{prefix}jsk_restart` - Restart the bot.",
            f"- `{prefix}jsk_update` - Update bot code and restart.",
            f"- `{prefix}jsk_load` - Load a cog.",
            f"- `{prefix}jsk_unload` - Unload a cog.",
            f"- `{prefix}jsk_reload` - Reload a cog.",
            f"- `{prefix}jsk_reloadall` - Reload all cogs.",
            f"- `{prefix}jsk_sync` - Sync or manage command tree.",
            f"- `{prefix}jsk_owners` - Manage bot owners.",
            f"- `{prefix}jsk_guilds` - List all guilds the bot is in.",
            f"- `{prefix}jsk_status` - Show bot status.",
            f"- `{prefix}jsk_extensions` - List all available cog files.",
            f"- `{prefix}jsk_test` - Test bot responsiveness.",
            f"- `{prefix}jsk_backup` - Create a code backup.",
            f"- `{prefix}jsk_invite` - Generate bot invite link.",
            f"- `{prefix}jsk_perms` - Check bot permissions.",
            f"- `{prefix}jsk_logs` - Show recent bot logs.",
            f"- `{prefix}jsk_clear` - Clear messages in the channel.",
            f"- `{prefix}jsk_ratelimits` - Show or reset command rate limits.",
            f"- `{prefix}jsk_source` - Show source code of a command, cog, or module."
        ]
        await self._send_paginated(ctx, commands_list, "Jishaku Debugging Commands")
        logger.info(f"{ctx.author} received jsk command list embed")

    @jishaku.command(name="shutdown", aliases=["stop"])
    async def jsk_shutdown(self, ctx):
        try:
            await ctx.send("Shutting down...")
            logger.info(f"{ctx.author} initiated shutdown")
            await self.bot.close()
        except discord.Forbidden as e:
            logger.error(f"Failed to send shutdown message: {e}")
            await self.bot.close()

    @jishaku.command(name="restart")
    async def jsk_restart(self, ctx):
        try:
            await ctx.send("Restarting...")
            logger.info(f"{ctx.author} initiated restart")
            with open("restart.json", "w", encoding="utf-8") as f:
                json.dump({"channel_id": ctx.channel.id}, f)
            try:
                python = sys.executable
                os.execl(python, python, *sys.argv)
            except Exception as e:
                logger.error(f"os.execl failed: {e}. Falling back to subprocess.")
                subprocess.Popen([sys.executable] + sys.argv)
                await self.bot.close()
        except discord.Forbidden as e:
            logger.error(f"Failed to send restart message: {e}")
            await self.bot.close()

    @jishaku.command(name="update")
    async def jsk_update(self, ctx):
        async with ctx.typing():
            try:
                process = await asyncio.create_subprocess_shell(
                    "git pull",
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                try:
                    stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=60.0)
                except asyncio.TimeoutError:
                    process.kill()
                    await ctx.send("Git pull timed out after 60 seconds.")
                    await self._report_error(ctx, "Git pull timeout", "jsk update")
                    return
                output = (stdout + stderr).decode("utf-8", errors="replace")
                await self._send_file(ctx, output, "git_output.txt")
                if process.returncode == 0:
                    await self.jsk_restart(ctx)
                else:
                    await ctx.send("Git pull failed; not restarting.")
            except (subprocess.SubprocessError, OSError) as e:
                await ctx.send(f"Error executing git pull:\n```py\n{str(e)}\n```")
                await self._report_error(ctx, str(e), "jsk update")
                logger.error(f"Git pull failed: {e}")

    @jishaku.command(name="load")
    async def jsk_load(self, ctx, *, cog: str):
        if not cog:
            await ctx.send("Please specify a cog to load.")
            return
        try:
            await self.bot.load_extension(cog)
            await ctx.send(f"Successfully loaded cog: `{cog}`")
            logger.info(f"{ctx.author} loaded cog: {cog}")
        except commands.ExtensionError as e:
            await ctx.send(f"Failed to load cog `{cog}`:\n```py\n{str(e)}\n```")
            await self._report_error(ctx, str(e), "jsk load")
            logger.error(f"Failed to load cog {cog}: {e}")

    @jishaku.command(name="unload")
    async def jsk_unload(self, ctx, *, cog: str):
        if not cog:
            await ctx.send("Please specify a cog to unload.")
            return
        if cog == "cogs.jishaku":
            await ctx.send("Cannot unload the Jishaku cog!")
            return
        if cog not in self.bot.extensions:
            await ctx.send(f"Cog `{cog}` is not loaded. Use `jsk extensions` to see loaded cogs.")
            return
        try:
            await self.bot.unload_extension(cog)
            await ctx.send(f"Successfully unloaded cog: `{cog}`")
            logger.info(f"{ctx.author} unloaded cog: {cog}")
        except commands.ExtensionError as e:
            await ctx.send(f"Failed to unload cog `{cog}`:\n```py\n{str(e)}\n```")
            await self._report_error(ctx, str(e), "jsk unload")
            logger.error(f"Failed to unload cog {cog}: {e}")

    @jishaku.command(name="reload")
    async def jsk_reload(self, ctx, *, cog: str):
        if not cog:
            await ctx.send("Please specify a cog to reload.")
            return
        if cog not in self.bot.extensions:
            await ctx.send(f"Cog `{cog}` is not loaded. Use `jsk extensions` to see loaded cogs.")
            return
        try:
            await self.bot.reload_extension(cog)
            await ctx.send(f"Successfully reloaded cog: `{cog}`")
            logger.info(f"{ctx.author} reloaded cog: {cog}")
        except commands.ExtensionError as e:
            await ctx.send(f"Failed to reload cog `{cog}`:\n```py\n{str(e)}\n```")
            await self._report_error(ctx, str(e), "jsk reload")
            logger.error(f"Failed to reload cog {cog}: {e}")

    @jishaku.command(name="reloadall")
    async def jsk_reloadall(self, ctx):
        async with ctx.typing():
            results = []
            for cog in list(self.bot.extensions.keys()):
                if cog == "cogs.jishaku":
                    results.append(f"- `{cog}`: Skipped (Jishaku)")
                    continue
                try:
                    await self.bot.reload_extension(cog)
                    results.append(f"- `{cog}`: Reloaded successfully")
                except commands.ExtensionError as e:
                    results.append(f"- `{cog}`: Failed - {str(e)}")
                    await self._report_error(ctx, str(e), "jsk reloadall")
            await self._send_paginated(ctx, results, "Reload All Cogs")
            logger.info(f"{ctx.author} reloaded all cogs")

    @jishaku.command(name="sync")
    async def jsk_sync(self, ctx, action: str = "sync", guild_id: int = None):
        async with ctx.typing():
            try:
                if not ctx.guild.me.guild_permissions.manage_guild:
                    await ctx.send("Bot lacks `Manage Guild` permission to sync commands.")
                    return
                if action.lower() == "sync":
                    if guild_id:
                        guild = self.bot.get_guild(guild_id)
                        if not guild:
                            await ctx.send(f"Guild ID `{guild_id}` not found.")
                            return
                        self.bot.tree.copy_global_to(guild=guild)
                        await self.bot.tree.sync(guild=guild)
                        await ctx.send(f"Command tree synced for guild ID: `{guild_id}`")
                    else:
                        await self.bot.tree.sync()
                        await ctx.send("Global command tree synced.")
                elif action.lower() == "clear":
                    if guild_id:
                        guild = self.bot.get_guild(guild_id)
                        if not guild:
                            await ctx.send(f"Guild ID `{guild_id}` not found.")
                            return
                        self.bot.tree.clear_commands(guild=guild)
                        await ctx.send(f"Command tree cleared for guild ID: `{guild_id}`")
                    else:
                        self.bot.tree.clear_commands(guild=None)
                        await ctx.send("Global command tree cleared.")
                elif action.lower() == "list":
                    commands = [f"- {cmd.name}" for cmd in self.bot.tree.get_commands()]
                    await self._send_paginated(ctx, commands, "Registered Slash Commands")
                else:
                    await ctx.send("Invalid action. Use `sync`, `clear`, or `list`.")
                logger.info(f"{ctx.author} ran sync action: {action} for guild: {guild_id}")
            except (discord.HTTPException, discord.app_commands.AppCommandError) as e:
                await ctx.send(f"Failed to {action} command tree:\n```py\n{str(e)}\n```")
                await self._report_error(ctx, str(e), f"jsk sync {action}")
                logger.error(f"Sync action {action} failed: {e}")

    @jishaku.command(name="owners")
    async def jsk_owners(self, ctx, action: str = "list", user: discord.User = None):
        try:
            if action.lower() == "list":
                if not self.owner_ids:
                    await ctx.send("No owners configured.")
                    return
                owners = [f"- <@{oid}> ({oid})" for oid in sorted(self.owner_ids)]
                await self._send_paginated(ctx, owners, "Bot Owners")
            elif action.lower() == "add":
                if not user:
                    await ctx.send("Please specify a user to add as an owner (e.g., `jsk owners add @user`).")
                    return
                if user.id in self.owner_ids:
                    await ctx.send(f"{user.mention} is already an owner.")
                    return
                self.owner_ids.add(user.id)
                self.config["owner_ids"] = list(self.owner_ids)
                self._save_config()
                await ctx.send(f"Added {user.mention} as an owner.")
            elif action.lower() == "remove":
                if not user:
                    await ctx.send("Please specify a user to remove as an owner (e.g., `jsk owners remove @user`).")
                    return
                if user.id not in self.owner_ids:
                    await ctx.send(f"{user.mention} is not an owner.")
                    return
                if len(self.owner_ids) <= 1:
                    await ctx.send("Cannot remove the last owner.")
                    return
                self.owner_ids.remove(user.id)
                self.config["owner_ids"] = list(self.owner_ids)
                self._save_config()
                await ctx.send(f"Removed {user.mention} as an owner.")
            else:
                await ctx.send("Invalid action. Use `list`, `add <user>`, or `remove <user>`.")
            logger.info(f"{ctx.author} ran owners action: {action} for user: {user.id if user else None}")
        except discord.Forbidden as e:
            logger.error(f"Failed to send owners message: {e}")
            await ctx.send("Failed to process owners command. Ensure the bot has permissions to send messages.")

    @jishaku.command(name="guilds")
    async def jsk_guilds(self, ctx):
        guilds = [
            f"- {g.name} (ID: {g.id}, Members: {g.member_count}, Owner: {g.owner})"
            for g in sorted(self.bot.guilds, key=lambda x: x.name)
        ]
        await self._send_paginated(ctx, guilds, "Guilds")
        logger.info(f"{ctx.author} listed guilds")

    @jishaku.command(name="status", aliases=["stats", "stat"])
    async def jsk_status(self, ctx):
        uptime = datetime.datetime.utcnow() - self.start_time
        uptime_str = str(uptime).split(".")[0]
        embed = discord.Embed(title="Bot Status", color=discord.Color.blue())
        embed.add_field(name="Guilds", value=len(self.bot.guilds), inline=True)
        embed.add_field(name="Users", value=len(self.bot.users), inline=True)
        embed.add_field(name="Latency", value=f"{self.bot.latency * 1000:.2f} ms", inline=True)
        embed.add_field(name="Commands", value=len(self.bot.commands), inline=True)
        embed.add_field(name="Uptime", value=uptime_str, inline=True)
        try:
            await ctx.send(embed=embed)
            logger.info(f"{ctx.author} ran status")
        except discord.Forbidden as e:
            logger.error(f"Failed to send status embed: {e}")
            await ctx.send("Failed to send status. Ensure the bot has permissions to send embeds.")

    @jishaku.command(name="extensions")
    async def jsk_extensions(self, ctx):
        cog_path = Path("cogs")
        if not cog_path.exists() or not cog_path.is_dir():
            await ctx.send("No `cogs` directory found.")
            return
        cogs = []
        for file in cog_path.glob("*.py"):
            if file.name == "__init__.py":
                continue
            cog_name = f"cogs.{file.stem}"
            status = " (loaded)" if cog_name in self.bot.extensions else ""
            cogs.append(f"- `{cog_name}`{status}")
        await self._send_paginated(ctx, sorted(cogs), "Available Cogs")
        logger.info(f"{ctx.author} listed extensions")

    @jishaku.command(name="test")
    async def jsk_test(self, ctx, *, response: str = "Pong!"):
        try:
            await ctx.send(response)
            logger.info(f"{ctx.author} ran test with response: {response}")
        except discord.Forbidden as e:
            logger.error(f"Failed to send test response: {e}")
            await ctx.send("Failed to send test response. Ensure the bot has permissions to send messages.")

    @jishaku.command(name="backup")
    async def jsk_backup(self, ctx, directories: str = "cogs"):
        async with ctx.typing():
            dir_list = directories.split() or ["cogs"]
            backup_dir = Path(self.config.get("backup_dir", "backups"))
            try:
                backup_dir.mkdir(exist_ok=True)
            except OSError as e:
                await ctx.send(f"Failed to create backup directory: {e}")
                return
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"backup_{timestamp}.zip"
            temp_dir = Path(f"temp_backup_{timestamp}")
            try:
                temp_dir.mkdir(exist_ok=True)
                for directory in dir_list:
                    dir_path = Path(directory)
                    if not dir_path.exists() or not dir_path.is_dir():
                        await ctx.send(f"Directory `{directory}` does not exist.")
                        return
                    shutil.copytree(dir_path, temp_dir / directory, dirs_exist_ok=True)
                shutil.make_archive(backup_dir / f"backup_{timestamp}", "zip", temp_dir)
                backup_path = backup_dir / backup_name
                if backup_path.stat().st_size > 25 * 1024 * 1024:
                    await ctx.send(f"Backup created at `{backup_path}` (too large to upload).")
                else:
                    try:
                        await ctx.send(f"Created backup: `{backup_name}`", file=discord.File(backup_path))
                        logger.info(f"{ctx.author} created backup of {', '.join(dir_list)}: {backup_name}")
                    except discord.Forbidden as e:
                        logger.error(f"Failed to send backup file: {e}")
                        await ctx.send("Failed to send backup file. Ensure the bot has permissions to send files.")
            except (shutil.Error, OSError) as e:
                await ctx.send(f"Failed to create backup:\n```py\n{str(e)}\n```")
                await self._report_error(ctx, str(e), "jsk backup")
                logger.error(f"Failed to create backup of {', '.join(dir_list)}: {e}")
            finally:
                try:
                    shutil.rmtree(temp_dir, ignore_errors=True)
                except OSError as e:
                    logger.warning(f"Failed to clean up temp backup directory: {e}")

    @jishaku.command(name="invite")
    async def jsk_invite(self, ctx):
        try:
            permissions = discord.Permissions(administrator=True)
            invite_url = discord.utils.oauth_url(
                self.bot.user.id,
                permissions=permissions,
                scopes=("bot", "applications.commands")
            )
            embed = discord.Embed(
                title="Bot Invite Link",
                description=f"[Click here to invite the bot]({invite_url})",
                color=discord.Color.blue()
            )
            await ctx.send(embed=embed)
            logger.info(f"{ctx.author} generated invite link")
        except discord.HTTPException as e:
            await ctx.send(f"Failed to generate invite link:\n```py\n{str(e)}\n```")
            await self._report_error(ctx, str(e), "jsk invite")
            logger.error(f"Failed to generate invite link: {e}")

    @jishaku.command(name="perms")
    async def jsk_perms(self, ctx, channel: discord.TextChannel = None):
        target = channel or ctx.channel
        try:
            perms = target.permissions_for(ctx.guild.me)
            perm_list = []
            for perm in dir(perms):
                if perm.startswith("_") or not isinstance(getattr(perms, perm), bool):
                    continue
                status = "✅" if getattr(perms, perm) else "❌"
                perm_name = perm.replace("_", " ").title()
                suggestion = " (Grant this for full functionality)" if not getattr(perms, perm) else ""
                perm_list.append(f"{status} {perm_name}{suggestion}")
            await self._send_paginated(ctx, perm_list, f"Permissions in {target.name}")
            logger.info(f"{ctx.author} checked permissions in {target.name}")
        except discord.Forbidden as e:
            await ctx.send(f"Failed to check permissions:\n```py\n{str(e)}\n```")
            await self._report_error(ctx, str(e), "jsk perms")
            logger.error(f"Failed to check permissions: {e}")

    @jishaku.command(name="logs")
    async def jsk_logs(self, ctx, lines: int = 20, level: str = None):
        if lines < 1 or lines > self.config.get("max_log_lines", 100):
            await ctx.send(f"Number of lines must be between 1 and {self.config.get('max_log_lines', 100)}.")
            return
        log_file = Path("bot.log")
        if not log_file.exists():
            await ctx.send("No log file found.")
            return
        try:
            with log_file.open("r", encoding="utf-8", errors="replace") as f:
                log_lines = []
                level = level.upper() if level else None
                for line in f:
                    if level and level not in line:
                        continue
                    log_lines.append(line.rstrip())
                    if len(log_lines) > lines:
                        log_lines.pop(0)
                output = "".join(f"{line}\n" for line in log_lines)
            if not output:
                await ctx.send("No logs match the specified criteria.")
                return
            await self._send_file(ctx, output, "logs.txt")
            logger.info(f"{ctx.author} viewed last {lines} log lines, level: {level}")
        except (IOError, UnicodeDecodeError) as e:
            await ctx.send(f"Failed to read log file:\n```py\n{str(e)}\n```")
            await self._report_error(ctx, str(e), "jsk logs")
            logger.error(f"Failed to read log file: {e}")

    @jishaku.command(name="clear")
    async def jsk_clear(self, ctx, amount: int = 10):
        if amount < 1 or amount > 100:
            await ctx.send("Amount must be between 1 and 100.")
            return
        try:
            if not ctx.channel.permissions_for(ctx.guild.me).manage_messages:
                await ctx.send("I don't have permission to manage messages.")
                return
            await ctx.channel.purge(limit=amount + 1)
            await ctx.send(f"Cleared {amount} messages.", delete_after=5)
            logger.info(f"{ctx.author} cleared {amount} messages in {ctx.channel.name}")
        except discord.Forbidden as e:
            await ctx.send("I don't have permission to manage messages.")
            await self._report_error(ctx, "Missing manage messages permission", "jsk clear")
            logger.error(f"Failed to clear messages: {e}")
        except discord.HTTPException as e:
            await ctx.send(f"Failed to clear messages:\n```py\n{str(e)}\n```")
            await self._report_error(ctx, str(e), "jsk clear")
            logger.error(f"Failed to clear messages: {e}")

    @jishaku.command(name="ratelimits")
    async def jsk_ratelimits(self, ctx, action: str = "list", command_name: str = None):
        try:
            if action.lower() == "list":
                cooldowns = []
                for command in self.bot.commands:
                    if command._buckets:
                        bucket = command._buckets.get_bucket({"channel_id": ctx.channel.id, "user_id": ctx.author.id})
                        if bucket and bucket._tokens < bucket._max:
                            remaining = bucket.get_remaining_time()
                            cooldowns.append(
                                f"- `{command.qualified_name}`: {bucket._tokens}/{bucket._max} uses remaining, "
                                f"resets in {remaining:.1f}s"
                            )
                if not cooldowns:
                    await ctx.send("No active cooldowns.")
                    return
                await self._send_paginated(ctx, cooldowns, "Command Rate Limits")
            elif action.lower() == "reset":
                if not command_name:
                    await ctx.send("Please specify a command to reset (e.g., `jsk ratelimits reset jsk logs`).")
                    return
                command = self.bot.get_command(command_name)
                if not command:
                    await ctx.send(f"Command `{command_name}` not found.")
                    return
                if not command._buckets:
                    await ctx.send(f"Command `{command_name}` has no cooldowns.")
                    return
                command._buckets.reset()
                await ctx.send(f"Cooldowns reset for `{command_name}`.")
            else:
                await ctx.send("Invalid action. Use `list` or `reset <command>`.")
            logger.info(f"{ctx.author} ran ratelimits action: {action} for command: {command_name}")
        except discord.Forbidden as e:
            logger.error(f"Failed to send ratelimits message: {e}")
            await ctx.send("Failed to process ratelimits command. Ensure the bot has permissions to send messages.")

    @jishaku.command(name="source")
    async def jsk_source(self, ctx, *, target: str):
        if not target:
            await ctx.send("Please specify a command, cog, or module to view.")
            return
        command = self.bot.get_command(target)
        if command:
            try:
                source = inspect.getsource(command.callback)
                source = textwrap.dedent(source)
                await self._send_file(ctx, source, f"{command.name}_source.py")
                logger.info(f"{ctx.author} viewed source of command: {target}")
            except (TypeError, OSError) as e:
                await ctx.send(f"Failed to get source for command `{target}`:\n```py\n{str(e)}\n```")
                await self._report_error(ctx, str(e), "jsk source")
                logger.error(f"Failed to get source for command {target}: {e}")
            return
        cog = self.bot.get_cog(target)
        if cog:
            try:
                source = inspect.getsource(cog.__class__)
                source = textwrap.dedent(source)
                await self._send_file(ctx, source, f"{cog.__class__.__name__}_source.py")
                logger.info(f"{ctx.author} viewed source of cog: {target}")
            except (TypeError, OSError) as e:
                await ctx.send(f"Failed to get source for cog `{target}`:\n```py\n{str(e)}\n```")
                await self._report_error(ctx, str(e), "jsk source")
                logger.error(f"Failed to get source for cog {target}: {e}")
            return
        try:
            module = sys.modules.get(target)
            if module:
                source = inspect.getsource(module)
                source = textwrap.dedent(source)
                await self._send_file(ctx, source, f"{target}_source.py")
                logger.info(f"{ctx.author} viewed source of module: {target}")
            else:
                await ctx.send(f"No command, cog, or module named `{target}` found.")
                logger.warning(f"{ctx.author} tried to view source of non-existent: {target}")
        except (TypeError, OSError) as e:
            await ctx.send(f"Failed to get source for module `{target}`:\n```py\n{str(e)}\n```")
            await self._report_error(ctx, str(e), "jsk source")
            logger.error(f"Failed to get source for module {target}: {e}")

async def setup(bot):
    try:
        # Check required intents
        required_intents = ["guilds", "members", "messages"]
        missing_intents = [intent for intent in required_intents if not getattr(bot.intents, intent)]
        if missing_intents:
            logger.error(f"Missing required intents: {', '.join(missing_intents)}")
            raise ValueError(f"Bot is missing required intents: {', '.join(missing_intents)}")

        # Load the cog
        cog = Jishaku(bot)
        await bot.add_cog(cog)
        logger.info("Jishaku cog loaded successfully")

        # Log registered commands
        registered_commands = []
        for cmd in bot.commands:
            if cmd.cog_name == "Jishaku":
                if isinstance(cmd, commands.Group):
                    subcommands = [f"{cmd.name} {subcmd.name}" for subcmd in cmd.commands]
                    registered_commands.append(f"{cmd.name} (Group with subcommands: {', '.join(subcommands)})")
                else:
                    registered_commands.append(cmd.qualified_name)
        logger.info(f"Registered Jishaku commands: {', '.join(registered_commands)}")
    except Exception as e:
        logger.error(f"Failed to load Jishaku cog: {e}\n{traceback.format_exc()}")
        raise
