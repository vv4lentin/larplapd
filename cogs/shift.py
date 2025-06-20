import discord
from discord import app_commands
from discord.ext import commands
import datetime

class Shift(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.LAPD_PERSONNEL_ROLE = 1292541838904791040
        self.LAPD_SENIOR_ROLE = 1383535858698948799
        self.SHIFT_LOG_CHANNEL_ID = 1292544821688537158
        self.data = {}  # In-memory data storage

    def now_ts(self):
        return int(datetime.datetime.now().timestamp())

    def humanize(self, seconds):
        m, s = divmod(int(seconds), 60)
        h, m = divmod(m, 60)
        return f"{h}h {m}m {s}s"

    def get_or_create_user(self, user_id):
        uid = str(user_id)
        if uid not in self.data:
            self.data[uid] = {"total": 0, "onduty": False, "start": 0, "onbreak": False, "breakstart": 0}
        return self.data[uid]

    async def get_or_create_status_roles(self, guild):
        on_duty_name = "Currently On-Duty"
        on_break_name = "Currently On-Break"
        on_duty_role = discord.utils.get(guild.roles, name=on_duty_name)
        on_break_role = discord.utils.get(guild.roles, name=on_break_name)
        if not on_duty_role:
            on_duty_role = await guild.create_role(
                name=on_duty_name, color=discord.Color.green(), reason="Shift system status role"
            )
        if not on_break_role:
            on_break_role = await guild.create_role(
                name=on_break_name, color=discord.Color.blue(), reason="Shift system status role"
            )
        return on_duty_role, on_break_role

    async def give_role(self, member, role):
        if role and role not in member.roles:
            await member.add_roles(role, reason="Shift Bot")

    async def remove_role(self, member, role):
        if role and role in member.roles:
            await member.remove_roles(role, reason="Shift Bot")

    async def log_shift_event(self, user, event):
        channel = self.bot.get_channel(self.SHIFT_LOG_CHANNEL_ID)
        if channel:
            embed = discord.Embed(
                title="Shift Log",
                description=f"**{user.mention}** {event}",
                color=discord.Color.teal(),
                timestamp=datetime.datetime.utcnow()
            )
            await channel.send(embed=embed)

    # -------- Shift Management Panel --------
    class ShiftManageView(discord.ui.View):
        def __init__(self, user, bot):
            super().__init__(timeout=120)
            self.user = user
            self.bot = bot
            udata = self.bot.cogs['Shift'].get_or_create_user(self.user.id)
            self.clear_items()
            if not udata["onduty"]:
                self.add_item(self.StartDuty())
            elif udata["onbreak"]:
                self.add_item(self.EndBreak())
                self.add_item(self.EndDuty())
            else:
                self.add_item(self.GoBreak())
                self.add_item(self.EndDuty())

        async def interaction_check(self, interaction):
            if interaction.user != self.user:
                await interaction.response.send_message(
                    "You can't control someone else's shift panel!", ephemeral=True
                )
                return False
            return True

        async def update_panel(self, interaction):
            view = self.__class__(self.user, self.bot)
            udata = self.bot.cogs['Shift'].get_or_create_user(self.user.id)
            total = udata["total"]
            live = self.bot.cogs['Shift'].now_ts() - udata["start"] if udata["onduty"] and not udata["onbreak"] else 0
            breaklive = self.bot.cogs['Shift'].now_ts() - udata["breakstart"] if udata["onbreak"] else 0
            status = "On Duty" if udata["onduty"] else "Off Duty"
            breakstatus = "On Break" if udata["onbreak"] else ("Active" if udata["onduty"] else "N/A")
            embed = discord.Embed(
                title=f"{self.user.display_name}'s Duty Panel",
                color=discord.Color.dark_blue()
            )
            if udata["onduty"] and not udata["onbreak"]:
                embed.add_field(name="Total Duty Time", value=f"`{self.bot.cogs['Shift'].humanize(total + live)}`", inline=False)
            elif udata["onbreak"]:
                embed.add_field(name="Total Duty Time", value=f"`{self.bot.cogs['Shift'].humanize(total)}`", inline=False)
                embed.add_field(name="Break Time", value=f"`{self.bot.cogs['Shift'].humanize(breaklive)}`", inline=False)
            else:
                embed.add_field(name="Total Duty Time", value=f"`{self.bot.cogs['Shift'].humanize(total)}`", inline=False)
            embed.add_field(name="Status", value=status, inline=True)
            embed.add_field(name="Break Status", value=breakstatus, inline=True)
            embed.set_footer(text="Shift System")
            try:
                await interaction.response.edit_message(embed=embed, view=view)
            except discord.InteractionResponded:
                await interaction.message.edit(embed=embed, view=view)

        class StartDuty(discord.ui.Button):
            def __init__(self):
                super().__init__(label="Start Duty", style=discord.ButtonStyle.green)

            async def callback(self, interaction: discord.Interaction):
                view: Shift.ShiftManageView = self.view
                udata = view.bot.cogs['Shift'].get_or_create_user(interaction.user.id)
                guild = interaction.guild
                on_duty_role, on_break_role = await view.bot.cogs['Shift'].get_or_create_status_roles(guild)
                if udata["onduty"]:
                    await interaction.response.send_message(embed=discord.Embed(
                        title="Already On Duty", color=discord.Color.orange()
                    ).set_footer(text="Shift System"), ephemeral=True)
                    return
                udata["onduty"] = True
                udata["start"] = view.bot.cogs['Shift'].now_ts()
                udata["onbreak"] = False
                udata["breakstart"] = 0
                await view.bot.cogs['Shift'].give_role(interaction.user, on_duty_role)
                await view.bot.cogs['Shift'].remove_role(interaction.user, on_break_role)
                await view.bot.cogs['Shift'].log_shift_event(interaction.user, "started their duty shift.")
                await view.update_panel(interaction)

        class GoBreak(discord.ui.Button):
            def __init__(self):
                super().__init__(label="Go On Break", style=discord.ButtonStyle.blurple)

            async def callback(self, interaction: discord.Interaction):
                view: Shift.ShiftManageView = self.view
                udata = view.bot.cogs['Shift'].get_or_create_user(interaction.user.id)
                guild = interaction.guild
                on_duty_role, on_break_role = await view.bot.cogs['Shift'].get_or_create_status_roles(guild)
                if not udata["onduty"]:
                    await interaction.response.send_message(embed=discord.Embed(
                        title="Not On Duty", color=discord.Color.red()
                    ).set_footer(text="Shift System"), ephemeral=True)
                    return
                if udata["onbreak"]:
                    await interaction.response.send_message(embed=discord.Embed(
                        title="Already On Break", color=discord.Color.orange()
                    ).set_footer(text="Shift System"), ephemeral=True)
                    return
                udata["onbreak"] = True
                udata["breakstart"] = view.bot.cogs['Shift'].now_ts()
                await view.bot.cogs['Shift'].give_role(interaction.user, on_break_role)
                await view.bot.cogs['Shift'].remove_role(interaction.user, on_duty_role)
                await view.bot.cogs['Shift'].log_shift_event(interaction.user, "went on break.")
                await view.update_panel(interaction)

        class EndBreak(discord.ui.Button):
            def __init__(self):
                super().__init__(label="End Break", style=discord.ButtonStyle.green)

            async def callback(self, interaction: discord.Interaction):
                view: Shift.ShiftManageView = self.view
                udata = view.bot.cogs['Shift'].get_or_create_user(interaction.user.id)
                guild = interaction.guild
                on_duty_role, on_break_role = await view.bot.cogs['Shift'].get_or_create_status_roles(guild)
                if not udata["onduty"] or not udata["onbreak"]:
                    await interaction.response.send_message(embed=discord.Embed(
                        title="Not On Break", color=discord.Color.orange()
                    ).set_footer(text="Shift System"), ephemeral=True)
                    return
                udata["onbreak"] = False
                udata["breakstart"] = 0
                await view.bot.cogs['Shift'].give_role(interaction.user, on_duty_role)
                await view.bot.cogs['Shift'].remove_role(interaction.user, on_break_role)
                await view.bot.cogs['Shift'].log_shift_event(interaction.user, "returned from break.")
                await view.update_panel(interaction)

        class EndDuty(discord.ui.Button):
            def __init__(self):
                super().__init__(label="End Duty", style=discord.ButtonStyle.red)

            async def callback(self, interaction: discord.Interaction):
                view: Shift.ShiftManageView = self.view
                udata = view.bot.cogs['Shift'].get_or_create_user(interaction.user.id)
                guild = interaction.guild
                on_duty_role, on_break_role = await view.bot.cogs['Shift'].get_or_create_status_roles(guild)
                if not udata["onduty"]:
                    await interaction.response.send_message(embed=discord.Embed(
                        title="Not On Duty", color=discord.Color.red()
                    ).set_footer(text="Shift System"), ephemeral=True)
                    return
                session_time = view.bot.cogs['Shift'].now_ts() - udata["start"] if udata["start"] else 0
                udata["total"] += session_time
                udata["onduty"] = False
                udata["onbreak"] = False
                udata["start"] = 0
                udata["breakstart"] = 0
                await view.bot.cogs['Shift'].remove_role(interaction.user, on_duty_role)
                await view.bot.cogs['Shift'].remove_role(interaction.user, on_break_role)
                await view.bot.cogs['Shift'].log_shift_event(interaction.user, f"ended their shift. ({view.bot.cogs['Shift'].humanize(session_time)} this session)")
                await view.update_panel(interaction)

    # -------- Shift Admin Panel --------
    class ShiftAdminPanel(discord.ui.View):
        def __init__(self, admin: discord.Member, target: discord.Member):
            super().__init__(timeout=90)
            self.admin = admin
            self.target = target

        async def interaction_check(self, interaction: discord.Interaction):
            if interaction.user != self.admin:
                await interaction.response.send_message("This panel is not for you.", ephemeral=True)
                return False
            return True

        @discord.ui.button(label="Add Time", style=discord.ButtonStyle.green)
        async def add_time(self, interaction: discord.Interaction, button: discord.ui.Button):
            await interaction.response.send_modal(self.AdminTimeModal(self.target, action="add"))

        @discord.ui.button(label="Subtract Time", style=discord.ButtonStyle.red)
        async def subtract_time(self, interaction: discord.Interaction, button: discord.ui.Button):
            await interaction.response.send_modal(self.AdminTimeModal(self.target, action="subtract"))

        @discord.ui.button(label="Wipe All", style=discord.ButtonStyle.grey)
        async def wipe_all(self, interaction: discord.Interaction, button: discord.ui.Button):
            udata = self.bot.cogs['Shift'].get_or_create_user(self.target.id)
            udata.update({"total": 0, "onduty": False, "start": 0, "onbreak": False, "breakstart": 0})
            embed = self.bot.cogs['Shift'].create_shift_admin_embed(self.target)
            await interaction.response.edit_message(embed=embed, view=self)
            await interaction.followup.send(f"All shift data wiped for {self.target.mention}.", ephemeral=True)

        class AdminTimeModal(discord.ui.Modal, title="Edit Shift Time"):
            minutes = discord.ui.TextInput(label="Minutes", style=discord.TextStyle.short, required=True, placeholder="Enter the number of minutes")

            def __init__(self, target: discord.Member, action: str):
                super().__init__()
                self.target = target
                self.action = action

            async def on_submit(self, interaction: discord.Interaction):
                try:
                    minutes = abs(float(self.minutes.value))
                    seconds = int(minutes * 60)  # Convert minutes to seconds
                except ValueError:
                    await interaction.response.send_message("Please enter a valid number of minutes.", ephemeral=True)
                    return
                udata = interaction.client.cogs['Shift'].get_or_create_user(self.target.id)
                if self.action == "add":
                    udata["total"] += seconds
                    msg = f"Added `{minutes:.2f}` minutes to {self.target.mention}."
                else:
                    udata["total"] = max(0, udata["total"] - seconds)
                    msg = f"Subtracted `{minutes:.2f}` minutes from {self.target.mention}."
                embed = interaction.client.cogs['Shift'].create_shift_admin_embed(self.target)
                await interaction.message.edit(embed=embed, view=interaction.client.cogs['Shift'].ShiftAdminPanel(interaction.user, self.target))
                await interaction.response.send_message(msg, ephemeral=True)

    def create_shift_admin_embed(self, target: discord.Member):
        udata = self.get_or_create_user(target.id)
        embed = discord.Embed(
            title=f"Shift Admin Panel: {target.display_name}",
            color=discord.Color.purple()
        )
        embed.add_field(name="Total Duty Time", value=f"`{self.humanize(udata['total'])}`", inline=False)
        embed.add_field(name="On Duty?", value="✅" if udata["onduty"] else "❌", inline=True)
        embed.add_field(name="On Break?", value="✅" if udata["onbreak"] else "❌", inline=True)
        embed.set_footer(text="Shift Admin Tools")
        return embed

    # -------- Shift Command Group --------
    @commands.hybrid_group(name="shift", description="Manage shift-related actions.")
    async def shift(self, ctx: commands.Context):
        if ctx.invoked_subcommand is None:
            await ctx.send("Invalid subcommand. Use `!shift manage`, `!shift leaderboard`, `!shift copylb`, `!shift active`, `!shift wipe`, or `!shift admin @user`.")

    @shift.command(name="manage", description="Open your shift management panel.")
    @app_commands.describe()
    async def manage(self, ctx: commands.Context):
        if not any(r.id in [self.LAPD_PERSONNEL_ROLE, self.LAPD_SENIOR_ROLE] for r in ctx.author.roles):
            await ctx.send(embed=discord.Embed(title="No Permission", description="You do not have permission to use this.", color=discord.Color.red()))
            return
        udata = self.get_or_create_user(ctx.author.id)
        total = udata["total"]
        live = self.now_ts() - udata["start"] if udata["onduty"] and not udata["onbreak"] else 0
        breaklive = self.now_ts() - udata["breakstart"] if udata["onbreak"] else 0
        status = "On Duty" if udata["onduty"] else "Off Duty"
        breakstatus = "On Break" if udata["onbreak"] else ("Active" if udata["onduty"] else "N/A")
        embed = discord.Embed(
            title=f"{ctx.author.display_name}'s Duty Panel",
            color=discord.Color.dark_blue()
        )
        if udata["onduty"] and not udata["onbreak"]:
            embed.add_field(name="Total Duty Time", value=f"`{self.humanize(total + live)}`", inline=False)
        elif udata["onbreak"]:
            embed.add_field(name="Total Duty Time", value=f"`{self.humanize(total)}`", inline=False)
            embed.add_field(name="Break Time", value=f"`{self.humanize(breaklive)}`", inline=False)
        else:
            embed.add_field(name="Total Duty Time", value=f"`{self.humanize(total)}`", inline=False)
        embed.add_field(name="Status", value=status, inline=True)
        embed.add_field(name="Break Status", value=breakstatus, inline=True)
        embed.set_footer(text="Shift System")
        await ctx.send(embed=embed, view=self.ShiftManageView(ctx.author, self.bot))

    @shift.command(name="leaderboard", description="Display the duty time leaderboard.")
    @app_commands.describe()
    async def leaderboard(self, ctx: commands.Context):
        if not any(r.id in [self.LAPD_PERSONNEL_ROLE, self.LAPD_SENIOR_ROLE] for r in ctx.author.roles):
            await ctx.send(embed=discord.Embed(title="No Permission", description="You do not have permission to use this.", color=discord.Color.red()))
            return
        leaderboard = []
        for m in ctx.guild.members:
            if any(r.id == self.LAPD_PERSONNEL_ROLE for r in m.roles):
                udata = self.get_or_create_user(m.id)
                total = udata["total"]
                if udata["onduty"] and not udata["onbreak"]:
                    total += self.now_ts() - udata["start"]
                leaderboard.append((m.display_name, total))
        leaderboard.sort(key=lambda x: x[1], reverse=True)
        desc = "\n".join(f"**{n}** — `{self.humanize(t)}`" for n, t in leaderboard)
        if not desc:
            desc = "No personnel found."
        embed = discord.Embed(
            title="Duty Leaderboard",
            description=desc,
            color=discord.Color.gold()
        )
        embed.set_footer(text="Shift System")
        await ctx.send(embed=embed)

    @shift.command(name="copylb", description="Copy the replied leaderboard embed and add your data to the actual leaderboard.")
    @app_commands.describe()
    async def copylb(self, ctx: commands.Context):
        if not any(r.id in [self.LAPD_PERSONNEL_ROLE, self.LAPD_SENIOR_ROLE] for r in ctx.author.roles):
            await ctx.send(embed=discord.Embed(
                title="No Permission",
                description="You do not have permission to use this.",
                color=discord.Color.red()
            ))
            return

        # Check if the command is a reply to a message
        if not ctx.message.reference or not ctx.message.reference.message_id:
            await ctx.send(embed=discord.Embed(
                title="No Reply",
                description="Please reply to a leaderboard message to use this command.",
                color=discord.Color.red()
            ))
            return

        try:
            # Fetch the replied message
            replied_message = await ctx.channel.fetch_message(ctx.message.reference.message_id)
            if not replied_message.embeds or replied_message.author != self.bot.user:
                await ctx.send(embed=discord.Embed(
                    title="Invalid Leaderboard",
                    description="The replied message is not a valid leaderboard embed from this bot.",
                    color=discord.Color.red()
                ))
                return

            # Get the leaderboard embed
            leaderboard_embed = replied_message.embeds[0]
            if leaderboard_embed.title != "Duty Leaderboard" or not leaderboard_embed.description:
                await ctx.send(embed=discord.Embed(
                    title="Invalid Leaderboard",
                    description="The replied message is not a valid leaderboard embed.",
                    color=discord.Color.red()
                ))
                return

            # Parse the existing leaderboard
            leaderboard = []
            lines = leaderboard_embed.description.split("\n")
            if lines == ["No personnel found."]:
                leaderboard = []
            else:
                for line in lines:
                    if " — " in line:
                        name, time_str = line.split(" — ")
                        name = name.strip("**")
                        time_str = time_str.strip("`")
                        leaderboard.append((name, time_str))

            # Function to convert time string to seconds
            def time_to_seconds(time_str):
                h, m, s = 0, 0, 0
                parts = time_str.split()
                for part in parts:
                    if part.endswith("h"):
                        h = int(part[:-1])
                    elif part.endswith("m"):
                        m = int(part[:-1])
                    elif part.endswith("s"):
                        s = int(part[:-1])
                return h * 3600 + m * 60 + s

            # Update self.data with leaderboard data
            for member in ctx.guild.members:
                for name, time_str in leaderboard:
                    if member.display_name == name:
                        udata = self.get_or_create_user(member.id)
                        udata["total"] = time_to_seconds(time_str)

            # Add or update the user's data
            udata = self.get_or_create_user(ctx.author.id)
            total = udata["total"]
            if udata["onduty"] and not udata["onbreak"]:
                total += self.now_ts() - udata["start"]
            leaderboard.append((ctx.author.display_name, self.humanize(total)))

            # Sort leaderboard by total time
            leaderboard.sort(key=lambda x: time_to_seconds(x[1]), reverse=True)

            # Create new description
            desc = "\n".join(f"**{n}** — `{t}`" for n, t in leaderboard)
            if not desc:
                desc = "No personnel found."

            # Create new embed
            embed = discord.Embed(
                title="Duty Leaderboard (Updated)",
                description=desc,
                color=discord.Color.gold()
            )
            embed.set_footer(text="Shift System")
            await ctx.send(embed=embed)

            # Log the event
            await self.log_shift_event(ctx.author, f"copied and updated the leaderboard with their data ({self.humanize(total)}).")

        except discord.errors.NotFound:
            await ctx.send(embed=discord.Embed(
                title="Error",
                description="The replied message could not be found.",
                color=discord.Color.red()
            ))
        except Exception as e:
            await ctx.send(embed=discord.Embed(
                title="Error",
                description=f"An error occurred: {str(e)}",
                color=discord.Color.red()
            ))

    @shift.command(name="active", description="List currently on-duty and on-break members.")
    @app_commands.describe()
    async def active(self, ctx: commands.Context):
        on_duty_role, on_break_role = await self.get_or_create_status_roles(ctx.guild)
        active = []
        on_break = []
        for m in ctx.guild.members:
            udata = self.get_or_create_user(m.id)
            if on_duty_role in m.roles and not udata["onbreak"]:
                live = self.now_ts() - udata.get("start", self.now_ts())
                total = udata["total"] + live
                active.append((m.display_name, self.humanize(total)))
            if on_break_role in m.roles and udata["onbreak"]:
                breaklive = self.now_ts() - udata.get("breakstart", self.now_ts())
                on_break.append((m.display_name, self.humanize(breaklive)))
        desc = ""
        if active:
            desc += "**On Duty:**\n" + "\n".join(f"{n} — `{t}`" for n, t in active) + "\n"
        if on_break:
            desc += "\n**On Break:**\n" + "\n".join(f"{n} — `{t}`" for n, t in on_break)
        if not desc:
            desc = "No one is currently on duty."
        embed = discord.Embed(
            title="Currently On Duty & On Break",
            description=desc,
            color=discord.Color.blue()
        )
        embed.set_footer(text="Shift System")
        await ctx.send(embed=embed)

    @shift.command(name="wipe", description="Wipe all shift data (Senior role only).")
    @app_commands.describe()
    async def wipe(self, ctx: commands.Context):
        if not any(r.id == self.LAPD_SENIOR_ROLE for r in ctx.author.roles):
            await ctx.send(embed=discord.Embed(
                title="No Permission",
                description="You do not have permission to use this.",
                color=discord.Color.red()
            ))
            return
        self.data.clear()  # Clear in-memory data
        await ctx.send(embed=discord.Embed(
            title="All Shift Data Wiped!",
            description="Every shift record has been reset. Note: Data will also reset when the bot restarts.",
            color=discord.Color.red()
        ))

    @shift.command(name="admin", description="Manage a user's shift data (Senior role only).")
    @app_commands.describe(member="The user to manage shift data for")
    async def admin(self, ctx: commands.Context, member: discord.Member = None):
        if not any(r.id == self.LAPD_SENIOR_ROLE for r in ctx.author.roles):
            await ctx.send(embed=discord.Embed(title="No Permission", description="You do not have permission.", color=discord.Color.red()))
            return
        if member is None:
            await ctx.send("Usage: !shift admin @user or /shift admin @user")
            return
        embed = self.create_shift_admin_embed(member)
        view = self.ShiftAdminPanel(ctx.author, member)
        await ctx.send(embed=embed, view=view)

async def setup(bot):
    await bot.add_cog(Shift(bot))
