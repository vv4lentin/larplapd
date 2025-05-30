import discord
from discord.ext import commands
from discord.utils import get
import datetime
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constants
PROMOTION_CHANNEL_ID = 1294705071400947742
INFRACTIONS_CHANNEL_ID = 1294705180775944264
WARNING_ROLE_IDS = [1306382455044964415, 1306382453283225650]
STRIKE_ROLE_IDS = [1306382451228016660, 1306382449378594867]
BLACKLIST_ROLE_ID = 1369681051508539476
INFRACTIONS_PERMS_ID = 1324855993846202398
PROMOTIONS_PERMS_ID = 1324855993846202398
BLACKLIST_PERMS_ID = 1324855993846202398
APPEAL_REVIEW_ROLE_ID = 1306381893515870209
INACTIVITY_ROLE_IDS = [1324540074834133033, 1324540189594353787]
INACTIVITY_PERMS_ID = 1324855993846202398

ROLE_HIERARCHY = [
    1306380858437144576, 1306380827143180340, 1306380805752361020, 1306380762542637150,
    1306380742007328868, 1306380723191812278, 1306380700194177085, 1306380648935591996,
    1306380625988554774, 1306380606799876197, 1306387881803120670, 1306387817311633428,
    1345207149344718859, 1345207148644401233, 1306380421717688380, 1306380397839515708,
    1306380287181324349, 1306380258185969716, 1323743686420594771, 1345207148149211229,
    1345207147398561873, 1306380183711780944, 1306380143752773662, 1306380120629444628,
    1306380038039408684
]

def get_active_roles(member, role_ids):
    return [r for r in member.roles if r.id in role_ids]

class LAPDManage(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="manage")
    async def staff_manage(self, ctx, member: discord.Member):
        # Check bot permissions
        bot_perms = ctx.guild.me.guild_permissions
        required_perms = ["manage_roles", "send_messages", "embed_links"]
        missing_perms = [perm for perm in required_perms if not getattr(bot_perms, perm)]
        if missing_perms:
            logger.error(f"Bot lacks permissions: {', '.join(missing_perms)}")
            return await ctx.send(f"🚫 Bot lacks required permissions: {', '.join(missing_perms)}")

        # Check if author has any of the required permission roles
        if not any(role.id in [INFRACTIONS_PERMS_ID, PROMOTIONS_PERMS_ID, BLACKLIST_PERMS_ID, INACTIVITY_PERMS_ID] for role in ctx.author.roles):
            logger.warning(f"{ctx.author} lacks permission to use staff_manage")
            return await ctx.send("🚫 You don’t have permission to use this command.")

        # Find the current hierarchy role and its index
        current_hierarchy_role = None
        current_index = -1
        for i, role_id in enumerate(ROLE_HIERARCHY):
            role = get(ctx.guild.roles, id=role_id)
            if role and role in member.roles:
                current_hierarchy_role = role
                current_index = i
                break
        current_rank = current_hierarchy_role.name if current_hierarchy_role else "None"

        # Determine previous rank
        previous_rank = "N/A"
        if current_index > 0:
            previous_role = get(ctx.guild.roles, id=ROLE_HIERARCHY[current_index - 1])
            previous_rank = previous_role.name if previous_role else "N/A"

        # Determine next rank
        next_rank = "N/A"
        if current_index < len(ROLE_HIERARCHY) - 1:
            next_role = get(ctx.guild.roles, id=ROLE_HIERARCHY[current_index + 1])
            next_rank = next_role.name if next_role else "N/A"

        active_warnings = get_active_roles(member, WARNING_ROLE_IDS)
        active_strikes = get_active_roles(member, STRIKE_ROLE_IDS)

        embed = discord.Embed(
            title=f"**{member.display_name}'s** LAPD Panel",
            description="Please select an action (Promotion, Warning, Strike, Demotion, Termination, Blacklist, Inactivity). Do not use this panel without permissions.",
            color=discord.Color.blue()
        )
        embed.add_field(name="Current Rank", value=current_rank, inline=True)
        embed.add_field(name="Previous Rank", value=previous_rank, inline=True)
        embed.add_field(name="Next Rank", value=next_rank, inline=True)
        embed.add_field(name="Active Warnings", value=str(len(active_warnings)), inline=True)
        embed.add_field(name="Active Strikes", value=str(len(active_strikes)), inline=True)

        view = StaffManageView(member, ctx.author)
        try:
            await ctx.send(embed=embed, view=view)
            logger.info(f"LAPD manage embed sent for {member}")
        except Exception as e:
            logger.error(f"Failed to send embed: {e}")
            await ctx.send("⚠️ Failed to display management panel. Please check bot permissions.")

class StaffManageView(discord.ui.View):
    def __init__(self, target, moderator):
        super().__init__(timeout=None)
        self.target = target
        self.moderator = moderator

    @discord.ui.button(label="Promotion", style=discord.ButtonStyle.primary)
    async def promote(self, interaction: discord.Interaction, button):
        if PROMOTIONS_PERMS_ID not in [role.id for role in self.moderator.roles]:
            logger.warning(f"{self.moderator} lacks promotion permissions")
            return await interaction.response.send_message("🚫 You lack promotion permissions.", ephemeral=True)
        await interaction.response.send_modal(PromotionModal(self.target, self.moderator))

    @discord.ui.button(label="Demotion", style=discord.ButtonStyle.danger)
    async def demote(self, interaction: discord.Interaction, button):
        if INFRACTIONS_PERMS_ID not in [role.id for role in self.moderator.roles]:
            logger.warning(f"{self.moderator} lacks infraction permissions")
            return await interaction.response.send_message("🚫 You lack infraction permissions.", ephemeral=True)
        await interaction.response.send_modal(DemotionModal(self.target, self.moderator))

    @discord.ui.button(label="Warning", style=discord.ButtonStyle.danger)
    async def warn(self, interaction: discord.Interaction, button):
        if INFRACTIONS_PERMS_ID not in [role.id for role in self.moderator.roles]:
            logger.warning(f"{self.moderator} lacks infraction permissions")
            return await interaction.response.send_message("🚫 You lack infraction permissions.", ephemeral=True)
        await interaction.response.send_modal(WarningModal(self.target, self.moderator))

    @discord.ui.button(label="Strike", style=discord.ButtonStyle.danger)
    async def strike(self, interaction: discord.Interaction, button):
        if INFRACTIONS_PERMS_ID not in [role.id for role in self.moderator.roles]:
            logger.warning(f"{self.moderator} lacks infraction permissions")
            return await interaction.response.send_message("🚫 You lack infraction permissions.", ephemeral=True)
        await interaction.response.send_modal(StrikeModal(self.target, self.moderator))

    @discord.ui.button(label="Termination", style=discord.ButtonStyle.danger)
    async def terminate(self, interaction: discord.Interaction, button):
        if INFRACTIONS_PERMS_ID not in [role.id for role in self.moderator.roles]:
            logger.warning(f"{self.moderator} lacks infraction permissions")
            return await interaction.response.send_message("🚫 You lack infraction permissions.", ephemeral=True)
        await interaction.response.send_modal(TerminationModal(self.target, self.moderator))

    @discord.ui.button(label="Blacklist", style=discord.ButtonStyle.danger)
    async def blacklist(self, interaction: discord.Interaction, button):
        if BLACKLIST_PERMS_ID not in [role.id for role in self.moderator.roles]:
            logger.warning(f"{self.moderator} lacks blacklist permissions")
            return await interaction.response.send_message("🚫 You lack blacklist permissions.", ephemeral=True)
        await interaction.response.send_modal(BlacklistModal(self.target, self.moderator))

    @discord.ui.button(label="Inactivity", style=discord.ButtonStyle.danger)
    async def inactivity(self, interaction: discord.Interaction, button):
        if INACTIVITY_PERMS_ID not in [role.id for role in self.moderator.roles]:
            logger.warning(f"{self.moderator} lacks inactivity permissions")
            return await interaction.response.send_message("🚫 You lack inactivity permissions.", ephemeral=True)
        await interaction.response.send_modal(InactivityModal(self.target, self.moderator))

class PromotionModal(discord.ui.Modal, title="Promotion"):
    def __init__(self, target: discord.Member, moderator: discord.Member):
        super().__init__()
        self.target = target
        self.moderator = moderator
        self.reason = discord.ui.TextInput(label="Reason", style=discord.TextStyle.paragraph, required=True)
        self.add_item(self.reason)

    async def on_submit(self, interaction: discord.Interaction):
        guild = interaction.guild
        channel = guild.get_channel(PROMOTION_CHANNEL_ID)
        if not channel:
            logger.error(f"Promotion channel {PROMOTION_CHANNEL_ID} not found")
            return await interaction.response.send_message("❌ Promotion channel not found.", ephemeral=True)

        bot_top_role = max([role for role in guild.me.roles], key=lambda r: r.position)
        current_role = None
        current_index = -1
        for i, role_id in enumerate(ROLE_HIERARCHY):
            role = get(guild.roles, id=role_id)
            if role and role in self.target.roles:
                current_role = role
                current_index = i
                break

        if current_index == -1:
            new_role = get(guild.roles, id=ROLE_HIERARCHY[0])
            if not new_role:
                logger.error(f"Lowest role {ROLE_HIERARCHY[0]} not found")
                return await interaction.response.send_message(f"❌ Lowest role not found.", ephemeral=True)
            if bot_top_role.position < new_role.position:
                logger.error(f"Bot's role is too low to assign {new_role.name}")
                return await interaction.response.send_message("❌ Bot's role is too low to assign this role.", ephemeral=True)
            try:
                await self.target.add_roles(new_role)
                logger.info(f"Added role {new_role.name} to {self.target}")
            except discord.Forbidden:
                logger.error(f"Failed to add role {new_role.name} to {self.target}: Missing permissions")
                return await interaction.response.send_message("❌ Bot lacks permission to add roles.", ephemeral=True)
        else:
            if current_index >= len(ROLE_HIERARCHY) - 1:
                logger.info(f"{self.target} is already at the highest role")
                return await interaction.response.send_message(f"❌ {self.target.display_name} is already at the highest role.", ephemeral=True)
            new_role = get(guild.roles, id=ROLE_HIERARCHY[current_index + 1])
            if not new_role:
                logger.error(f"Next role {ROLE_HIERARCHY[current_index + 1]} not found")
                return await interaction.response.send_message(f"❌ Next role not found.", ephemeral=True)
            if bot_top_role.position < new_role.position:
                logger.error(f"Bot's role is too low to assign {new_role.name}")
                return await interaction.response.send_message("❌ Bot's role is too low to assign this role.", ephemeral=True)
            try:
                await self.target.add_roles(new_role)
                await self.target.remove_roles(current_role)
                logger.info(f"Updated roles for {self.target}: Added {new_role.name}, Removed {current_role.name}")
            except discord.Forbidden:
                logger.error(f"Failed to update roles for {self.target}: Missing permissions")
                return await interaction.response.send_message("❌ Bot lacks permission to manage roles.", ephemeral=True)

        embed = discord.Embed(
            title="📈 Promotion Notice",
            color=discord.Color.green()
        )
        embed.add_field(name="Officer", value=self.target.mention, inline=True)
        embed.add_field(name="New Role", value=new_role.mention, inline=True)
        embed.add_field(name="Reason", value=f"> {self.reason.value}", inline=False)
        embed.set_footer(text=f"Issued by {self.moderator.display_name} • {datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")

        try:
            await channel.send(self.target.mention)
            await channel.send(embed=embed)
            logger.info(f"Promotion notice sent to channel {channel.name}")
            try:
                await self.target.send(embed=embed)
                logger.info(f"Promotion notice DM sent to {self.target}")
            except discord.Forbidden:
                logger.warning(f"Failed to send DM to {self.target}")
        except discord.Forbidden:
            logger.error(f"Failed to send promotion notice to channel {channel.name}: Missing permissions")
            await interaction.response.send_message("⚠️ Promotion processed, but I lack permission to send messages in the promotion channel.", ephemeral=True)

        await interaction.response.send_message("✅ Promotion submitted.", ephemeral=True)

class DemotionModal(discord.ui.Modal, title="Demotion"):
    def __init__(self, target: discord.Member, moderator: discord.Member):
        super().__init__()
        self.target = target
        self.moderator = moderator
        self.reason = discord.ui.TextInput(label="Reason for Demotion", style=discord.TextStyle.paragraph, required=True)
        self.add_item(self.reason)

    async def on_submit(self, interaction: discord.Interaction):
        guild = interaction.guild
        channel = guild.get_channel(INFRACTIONS_CHANNEL_ID)
        if not channel:
            logger.error(f"Infractions channel {INFRACTIONS_CHANNEL_ID} not found")
            return await interaction.response.send_message("❌ Infractions channel not found.", ephemeral=True)

        bot_top_role = max([role for role in guild.me.roles], key=lambda r: r.position)
        current_role = None
        current_index = -1
        for i, role_id in enumerate(ROLE_HIERARCHY):
            role = get(guild.roles, id=role_id)
            if role and role in self.target.roles:
                current_role = role
                current_index = i
                break

        if current_index <= 0:
            logger.info(f"{self.target} is at the lowest role or has no hierarchy role")
            return await interaction.response.send_message(f"❌ {self.target.display_name} is at the lowest role or has no hierarchy role.", ephemeral=True)

        new_role = get(guild.roles, id=ROLE_HIERARCHY[current_index - 1])
        if not new_role:
            logger.error(f"Previous role {ROLE_HIERARCHY[current_index - 1]} not found")
            return await interaction.response.send_message(f"❌ Previous role not found.", ephemeral=True)

        if bot_top_role.position < new_role.position or (current_role and bot_top_role.position < current_role.position):
            logger.error(f"Bot's role is too low to manage {new_role.name} or {current_role.name}")
            return await interaction.response.send_message("❌ Bot's role is too low to manage these roles.", ephemeral=True)

        try:
            await self.target.add_roles(new_role)
            await self.target.remove_roles(current_role)
            logger.info(f"Updated roles for {self.target}: Added {new_role.name}, Removed {current_role.name}")
        except discord.Forbidden:
            logger.error(f"Failed to update roles for {self.target}: Missing permissions")
            return await interaction.response.send_message("❌ Bot lacks permission to manage roles.", ephemeral=True)

        embed = discord.Embed(
            title="📉 Demotion Notice",
            color=discord.Color.red()
        )
        embed.add_field(name="Officer", value=self.target.mention, inline=True)
        embed.add_field(name="New Role", value=new_role.mention, inline=True)
        embed.add_field(name="Reason", value=f"> {self.reason.value}", inline=False)
        embed.set_footer(text=f"Issued by {self.moderator.display_name} • {datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")

        try:
            await channel.send(self.target.mention)
            await channel.send(embed=embed, view=AppealView(self.target, "Demotion"))
            logger.info(f"Demotion notice sent to channel {channel.name}")
            try:
                await self.target.send(embed=embed)
                logger.info(f"Demotion notice DM sent to {self.target}")
            except discord.Forbidden:
                logger.warning(f"Failed to send DM to {self.target}")
        except discord.Forbidden:
            logger.error(f"Failed to send demotion notice to channel {channel.name}: Missing permissions")
            await interaction.response.send_message("⚠️ Demotion processed, but I lack permission to send messages in the infractions channel.", ephemeral=True)

        await interaction.response.send_message("✅ Demotion submitted.", ephemeral=True)

class WarningModal(discord.ui.Modal, title="Issue Warning"):
    def __init__(self, target: discord.Member, moderator: discord.Member):
        super().__init__()
        self.target = target
        self.moderator = moderator
        self.reason = discord.ui.TextInput(label="Reason", style=discord.TextStyle.paragraph, required=True)
        self.add_item(self.reason)

    async def on_submit(self, interaction: discord.Interaction):
        guild = interaction.guild
        channel = guild.get_channel(INFRACTIONS_CHANNEL_ID)
        if not channel:
            logger.error(f"Infractions channel {INFRACTIONS_CHANNEL_ID} not found")
            return await interaction.response.send_message("❌ Infractions channel not found.", ephemeral=True)

        bot_top_role = max([role for role in guild.me.roles], key=lambda r: r.position)
        active_warnings = get_active_roles(self.target, WARNING_ROLE_IDS)
        next_warning_role = WARNING_ROLE_IDS[len(active_warnings)] if len(active_warnings) < len(WARNING_ROLE_IDS) else WARNING_ROLE_IDS[-1]
        role = get(guild.roles, id=next_warning_role)
        if not role:
            logger.error(f"Warning role {next_warning_role} not found")
            return await interaction.response.send_message(f"❌ Warning role not found.", ephemeral=True)

        if bot_top_role.position < role.position:
            logger.error(f"Bot's role is too low to assign {role.name}")
            return await interaction.response.send_message("❌ Bot's role is too low to assign this role.", ephemeral=True)

        try:
            await self.target.add_roles(role)
            logger.info(f"Added warning role {role.name} to {self.target}")
        except discord.Forbidden:
            logger.error(f"Failed to add warning role {role.name} to {self.target}: Missing permissions")
            return await interaction.response.send_message("❌ Bot lacks permission to add roles.", ephemeral=True)

        embed = discord.Embed(
            title=f"⚠️ Warning • {role.name}",
            color=discord.Color.red()
        )
        embed.add_field(name="Officer", value=self.target.mention, inline=True)
        embed.add_field(name="Active Warnings", value=str(len(active_warnings) + 1), inline=True)
        embed.add_field(name="Reason", value=f"> {self.reason.value}", inline=False)
        embed.set_footer(text=f"Issued by {self.moderator.display_name} • {datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")

        try:
            await channel.send(self.target.mention)
            await channel.send(embed=embed, view=AppealView(self.target, "Warning"))
            logger.info(f"Warning notice sent to channel {channel.name}")
            try:
                await self.target.send(embed=embed)
                logger.info(f"Warning notice DM sent to {self.target}")
            except discord.Forbidden:
                logger.warning(f"Failed to send DM to {self.target}")
        except discord.Forbidden:
            logger.error(f"Failed to send warning notice to channel {channel.name}: Missing permissions")
            await interaction.response.send_message("⚠️ Warning processed, but I lack permission to send messages in the infractions channel.", ephemeral=True)

        await interaction.response.send_message("✅ Warning issued.", ephemeral=True)

class StrikeModal(discord.ui.Modal, title="Issue Strike"):
    def __init__(self, target: discord.Member, moderator: discord.Member):
        super().__init__()
        self.target = target
        self.moderator = moderator
        self.reason = discord.ui.TextInput(label="Reason", style=discord.TextStyle.paragraph, required=True)
        self.add_item(self.reason)

    async def on_submit(self, interaction: discord.Interaction):
        guild = interaction.guild
        channel = guild.get_channel(INFRACTIONS_CHANNEL_ID)
        if not channel:
            logger.error(f"Infractions channel {INFRACTIONS_CHANNEL_ID} not found")
            return await interaction.response.send_message("❌ Infractions channel not found.", ephemeral=True)

        bot_top_role = max([role for role in guild.me.roles], key=lambda r: r.position)
        active_strikes = get_active_roles(self.target, STRIKE_ROLE_IDS)
        next_strike_role = STRIKE_ROLE_IDS[len(active_strikes)] if len(active_strikes) < len(STRIKE_ROLE_IDS) else STRIKE_ROLE_IDS[-1]
        role = get(guild.roles, id=next_strike_role)
        if not role:
            logger.error(f"Strike role {next_strike_role} not found")
            return await interaction.response.send_message(f"❌ Strike role not found.", ephemeral=True)

        if bot_top_role.position < role.position:
            logger.error(f"Bot's role is too low to assign {role.name}")
            return await interaction.response.send_message("❌ Bot's role is too low to assign this role.", ephemeral=True)

        try:
            await self.target.add_roles(role)
            logger.info(f"Added strike role {role.name} to {self.target}")
        except discord.Forbidden:
            logger.error(f"Failed to add strike role {role.name} to {self.target}: Missing permissions")
            return await interaction.response.send_message("❌ Bot lacks permission to add roles.", ephemeral=True)

        embed = discord.Embed(
            title=f"❌ Strike • {role.name}",
            color=discord.Color.red()
        )
        embed.add_field(name="Officer", value=self.target.mention, inline=True)
        embed.add_field(name="Active Strikes", value=str(len(active_strikes) + 1), inline=True)
        embed.add_field(name="Reason", value=f"> {self.reason.value}", inline=False)
        embed.set_footer(text=f"Issued by {self.moderator.display_name} • {datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")

        try:
            await channel.send(self.target.mention)
            await channel.send(embed=embed, view=AppealView(self.target, "Strike"))
            logger.info(f"Strike notice sent to channel {channel.name}")
            try:
                await self.target.send(embed=embed)
                logger.info(f"Strike notice DM sent to {self.target}")
            except discord.Forbidden:
                logger.warning(f"Failed to send DM to {self.target}")
        except discord.Forbidden:
            logger.error(f"Failed to send strike notice to channel {channel.name}: Missing permissions")
            await interaction.response.send_message("⚠️ Strike processed, but I lack permission to send messages in the infractions channel.", ephemeral=True)

        await interaction.response.send_message("✅ Strike issued.", ephemeral=True)

class TerminationModal(discord.ui.Modal, title="Terminate Staff"):
    def __init__(self, target: discord.Member, moderator: discord.Member):
        super().__init__()
        self.target = target
        self.moderator = moderator
        self.reason = discord.ui.TextInput(label="Reason for termination", style=discord.TextStyle.paragraph, required=True)
        self.add_item(self.reason)

    async def on_submit(self, interaction: discord.Interaction):
        guild = interaction.guild
        channel = guild.get_channel(INFRACTIONS_CHANNEL_ID)
        if not channel:
            logger.error(f"Infractions channel {INFRACTIONS_CHANNEL_ID} not found")
            return await interaction.response.send_message("❌ Infractions channel not found.", ephemeral=True)

        embed = discord.Embed(
            title="🚫 Termination Notice",
            description=f"{self.target.mention} has been terminated from the LAPD.",
            color=discord.Color.red()
        )
        embed.add_field(name="Reason", value=f"> {self.reason.value}", inline=False)
        embed.set_footer(text=f"Issued by {self.moderator.display_name} • {datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")

        try:
            await channel.send(self.target.mention)
            await channel.send(embed=embed, view=AppealView(self.target, "Termination"))
            logger.info(f"Termination notice sent to channel {channel.name}")
            try:
                await self.target.send(embed=embed)
                logger.info(f"Termination notice DM sent to {self.target}")
            except discord.Forbidden:
                logger.warning(f"Failed to send DM to {self.target}")
        except discord.Forbidden:
            logger.error(f"Failed to send termination notice to channel {channel.name}: Missing permissions")
            await interaction.response.send_message("⚠️ Termination processed, but I lack permission to send messages in the infractions channel.", ephemeral=True)

        await interaction.response.send_message("✅ Termination processed.", ephemeral=True)

class BlacklistModal(discord.ui.Modal, title="Blacklist Staff"):
    def __init__(self, target: discord.Member, moderator: discord.Member):
        super().__init__()
        self.target = target
        self.moderator = moderator
        self.reason = discord.ui.TextInput(label="Reason for blacklist", style=discord.TextStyle.paragraph, required=True)
        self.add_item(self.reason)

    async def on_submit(self, interaction: discord.Interaction):
        guild = interaction.guild
        channel = guild.get_channel(INFRACTIONS_CHANNEL_ID)
        if not channel:
            logger.error(f"Infractions channel {INFRACTIONS_CHANNEL_ID} not found")
            return await interaction.response.send_message("❌ Infractions channel not found.", ephemeral=True)

        bot_top_role = max([role for role in guild.me.roles], key=lambda r: r.position)
        blacklist_role = get(guild.roles, id=BLACKLIST_ROLE_ID)
        if not blacklist_role:
            logger.error(f"Blacklist role {BLACKLIST_ROLE_ID} not found")
            return await interaction.response.send_message(f"❌ Blacklist role not found.", ephemeral=True)

        if bot_top_role.position < blacklist_role.position:
            logger.error(f"Bot's role is too low to assign {blacklist_role.name}")
            return await interaction.response.send_message("❌ Bot's role is too low to assign this role.", ephemeral=True)

        try:
            await self.target.add_roles(blacklist_role)
            logger.info(f"Added blacklist role {blacklist_role.name} to {self.target}")
        except discord.Forbidden:
            logger.error(f"Failed to add blacklist role to {self.target}: Missing permissions")
            return await interaction.response.send_message("⚠️ Blacklist processed, but I lack permission to add the blacklist role.", ephemeral=True)

        embed = discord.Embed(
            title="⛔ Blacklist Notice",
            description=f"{self.target.mention} has been blacklisted from the LAPD. They cannot re-apply or be part of the LAPD anymore. They can still appeal it for a chance to reverse it.",
            color=discord.Color.dark_red()
        )
        embed.add_field(name="Reason", value=f"> {self.reason.value}", inline=False)
        embed.add_field(name="Blacklist Role", value=blacklist_role.mention, inline=True)
        embed.set_footer(text=f"Issued by {self.moderator.display_name} • {datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")

        try:
            await channel.send(self.target.mention)
            await channel.send(embed=embed, view=AppealView(self.target, "Blacklist"))
            logger.info(f"Blacklist notice sent to channel {channel.name}")
            try:
                await self.target.send(embed=embed)
                logger.info(f"Blacklist notice DM sent to {self.target}")
            except discord.Forbidden:
                logger.warning(f"Failed to send DM to {self.target}")
        except discord.Forbidden:
            logger.error(f"Failed to send blacklist notice to channel {channel.name}: Missing permissions")
            await interaction.response.send_message("⚠️ Blacklist processed, but I lack permission to send messages in the infractions channel.", ephemeral=True)

        await interaction.response.send_message("✅ Blacklist processed.", ephemeral=True)

class InactivityModal(discord.ui.Modal, title="Issue Inactivity Notice"):
    def __init__(self, target: discord.Member, moderator: discord.Member):
        super().__init__()
        self.target = target
        self.moderator = moderator
        self.reason = discord.ui.TextInput(label="Reason for Inactivity Notice", style=discord.TextStyle.paragraph, required=True)
        self.add_item(self.reason)

    async def on_submit(self, interaction: discord.Interaction):
        guild = interaction.guild
        channel = guild.get_channel(INFRACTIONS_CHANNEL_ID)
        if not channel:
            logger.error(f"Infractions channel {INFRACTIONS_CHANNEL_ID} not found")
            return await interaction.response.send_message("❌ Infractions channel not found.", ephemeral=True)

        bot_top_role = max([role for role in guild.me.roles], key=lambda r: r.position)
        active_inactivity = get_active_roles(self.target, INACTIVITY_ROLE_IDS)
        next_inactivity_role = INACTIVITY_ROLE_IDS[len(active_inactivity)] if len(active_inactivity) < len(INACTIVITY_ROLE_IDS) else INACTIVITY_ROLE_IDS[-1]
        role = get(guild.roles, id=next_inactivity_role)
        if not role:
            logger.error(f"Inactivity role {next_inactivity_role} not found")
            return await interaction.response.send_message(f"❌ Inactivity role not found.", ephemeral=True)

        if bot_top_role.position < role.position:
            logger.error(f"Bot's role is too low to assign {role.name}")
            return await interaction.response.send_message("❌ Bot's role is too low to assign this role.", ephemeral=True)

        try:
            await self.target.add_roles(role)
            logger.info(f"Added inactivity role {role.name} to {self.target}")
        except discord.Forbidden:
            logger.error(f"Failed to add inactivity role {role.name} to {self.target}: Missing permissions")
            return await interaction.response.send_message("❌ Bot lacks permission to add roles.", ephemeral=True)

        embed = discord.Embed(
            title=f"🕒 Inactivity Notice • {role.name}",
            color=discord.Color.orange(),
            description=f"{self.target.mention} has been issued an inactivity notice."
        )
        embed.add_field(name="Member", value=self.target.mention, inline=True)
        embed.add_field(name="Active Inactivity Notices", value=str(len(active_inactivity) + 1), inline=True)
        embed.add_field(name="Reason", value=f"> {self.reason.value}", inline=False)
        embed.set_footer(text=f"Issued by {self.moderator.display_name} • {datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")

        try:
            await channel.send(self.target.mention)
            await channel.send(embed=embed, view=AppealView(self.target, "Inactivity"))
            logger.info(f"Inactivity notice sent to channel {channel.name}")
            try:
                await self.target.send(embed=embed)
                logger.info(f"Inactivity notice DM sent to {self.target}")
            except discord.Forbidden:
                logger.warning(f"Failed to send DM to {self.target}")
        except discord.Forbidden:
            logger.error(f"Failed to send inactivity notice to channel {channel.name}: Missing permissions")
            await interaction.response.send_message("⚠️ Inactivity notice processed, but I lack permission to send messages in the infractions channel.", ephemeral=True)

        await interaction.response.send_message("✅ Inactivity notice issued.", ephemeral=True)

class AppealView(discord.ui.View):
    def __init__(self, target: discord.Member, infraction_type: str):
        super().__init__(timeout=None)
        self.target = target
        self.infraction_type = infraction_type

    @discord.ui.button(label="Appeal", style=discord.ButtonStyle.secondary)
    async def appeal(self, interaction: discord.Interaction, button):
        if not interaction.channel.permissions_for(interaction.guild.me).create_private_threads:
            logger.error(f"Bot lacks permission to create private threads in {interaction.channel.name}")
            return await interaction.response.send_message("❌ Bot lacks permission to create private threads.", ephemeral=True)
        
        try:
            thread = await interaction.channel.create_thread(
                name=f"Infractions Appeal: {self.infraction_type} of {self.target.display_name}",
                type=discord.ChannelType.private_thread
            )
            await thread.add_user(self.target)
            await thread.send(f"{self.target.mention}, you may appeal your {self.infraction_type.lower()} here. <@&{APPEAL_REVIEW_ROLE_ID}> Please review the infraction; if this is a blacklist, please ping a SHR.")
            logger.info(f"Appeal thread created for {self.target}: {self.infraction_type}")
            await interaction.response.send_message("✅ Appeal thread created.", ephemeral=True)
        except discord.Forbidden:
            logger.error(f"Failed to create appeal thread: Missing permissions")
            await interaction.response.send_message("❌ Failed to create appeal thread. Bot lacks permission to create threads.", ephemeral=True)
        except Exception as e:
            logger.error(f"Failed to create appeal thread: {e}")
            await interaction.response.send_message("❌ An error occurred while creating the appeal thread.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(LAPDManage(bot))
