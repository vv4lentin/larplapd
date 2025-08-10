import discord
from discord.ext import commands
from datetime import datetime
import os
import asyncio
import json
import keep_alive
import time
import re
from collections import Counter
from keep_alive import keep_alive

# Configuration
GUILD_ID = 1292523481539543193  # Your guild ID
BOT_TOKEN = os.getenv("BOT_TOKEN") or "MTM3NTk3NzI4Mjg1MzY3MTExMw.GsT2gi.9KQThQd57nEbRNHm1bEO2uOoE1BnAydsDiqjWA"  # Replace with your bot token
SHARED_PANEL_CHANNEL = 123456789012345678  # Replace with shared panel channel ID for Sub-Divisions
ANNOUNCEMENT_CHANNEL_ID = 1292541250775290097
ALLOWED_ROLE_IDS = [1337050305153470574, 1361565373593292851]
HR_ROLE_IDS = [1324522426771443813, 1339058176003407915]
AUTOROLE_ROLE_ID = 1292541718033596558

# Bot setup with intents
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True
intents.presences = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Application configuration
APPLICATIONS = {
    'lapd_entry': {
        'name': 'LAPD | Entry',
        'questions': [
            'Why do you want to join the LAPD?',
            'What is your experience with roleplay?',
            'How familiar are you with our server rules?'
        ],
        'review_channel': 123456789012345678,  # Replace with channel ID
        'panel_channel': 123456789012345678,   # Replace with LAPD panel channel ID
        'role_id': 123456789012345678,        # Replace with role ID
        'ping_role': 123456789012345678,      # Replace with ping role/user ID
        'panel_name': 'Los Angeles Police Department Entry Application',
        'panel_desc': (
            "Please click the button below to start the application.\n\n"
            "**Requirements:**\n"
            "- You must be 14 or older\n"
            "- You must have a decent SPaG\n"
            "- You must use common sense\n"
            "- You must be able to complete a minimum of 2 hours of duty per week\n"
            "- You must be dedicated in the department\n"
            "- You must be capable to answer questions\n"
            "- You may not use AI\n\n"
            "Good luck!"
        ),
        'input_type': 'button'
    },
    'gang_unit': {
        'name': 'Gang Unit | Entry',
        'questions': [
            'What experience do you have with gang-related roleplay?',
            'How would you handle a gang conflict scenario?',
            'What is your availability for patrols?'
        ],
        'review_channel': 123456789012345678,  # Replace with channel ID
        'panel_channel': SHARED_PANEL_CHANNEL,  # Shared panel channel
        'role_id': 123456789012345678,        # Replace with role ID
        'ping_role': 123456789012345678,      # Replace with ping role/user ID
        'dropdown_label': 'Gang Unit Application'
    },
    'swat_entry': {
        'name': 'SWAT | Entry',
        'questions': [
            'What tactical experience do you have in roleplay?',
            'Describe a high-pressure situation you’ve managed.',
            'Why do you want to join SWAT?'
        ],
        'review_channel': 123456789012345678,  # Replace with channel ID
        'panel_channel': SHARED_PANEL_CHANNEL,  # Shared panel channel
        'role_id': 123456789012345678,        # Replace with role ID
        'ping_role': 123456789012345678,      # Replace with ping role/user ID
        'dropdown_label': 'SWAT Application'
    },
    'internal_affairs': {
        'name': 'Internal Affairs',
        'questions': [
            'What experience do you have investigating misconduct?',
            'How would you ensure impartiality in investigations?',
            'What motivates you to join Internal Affairs?'
        ],
        'review_channel': 123456789012345678,  # Replace with channel ID
        'panel_channel': SHARED_PANEL_CHANNEL,  # Shared panel channel
        'role_id': 123456789012345678,        # Replace with role ID
        'ping_role': 123456789012345678,      # Replace with ping role/user ID
        'dropdown_label': 'IA Application'
    },
    'field_training': {
        'name': 'Field Training Program',
        'questions': [
            'What experience do you have training others?',
            'How would you teach a new recruit our procedures?',
            'What is your approach to mentorship?'
        ],
        'review_channel': 123456789012345678,  # Replace with channel ID
        'panel_channel': SHARED_PANEL_CHANNEL,  # Shared panel channel
        'role_id': 123456789012345678,        # Replace with role ID
        'ping_role': 123456789012345678,      # Replace with ping role/user ID
        'dropdown_label': 'FTO Application'
    },
    'sergeant': {
        'name': 'Sergeant',
        'questions': [
            'What leadership experience do you have?',
            'How would you manage a team of officers?',
            'Why do you believe you’re ready for Sergeant?'
        ],
        'review_channel': 123456789012345678,  # Replace with channel ID
        'panel_channel': 123456789012345678,   # Replace with Sergeant panel channel ID
        'role_id': 123456789012345678,        # Replace with role ID
        'ping_role': 123456789012345678,      # Replace with ping role/user ID
        'panel_name': 'Sergeant Application',
        'panel_desc': (
            "Please click the button below to start the application.\n\n"
            "**Requirements:**\n"
            "- You must be PO III+I\n"
            "- You must have a decent SPaG\n"
            "- You must use common sense\n"
            "- You must be capable to answer questions\n"
            "- You may not use AI\n\n"
            "Good luck!"
        ),
        'input_type': 'button'
    },
    'final_exam': {
        'name': 'Final Exam',
        'questions': [
            'How have you prepared for the LAPD Final Exam?',
            'What areas of our training do you feel most confident in?',
            'How will you apply your training in real scenarios?'
        ],
        'review_channel': 123456789012345678,  # Replace with channel ID
        'panel_channel': 123456789012345678,   # Replace with Final Exam panel channel ID
        'role_id': 123456789012345678,        # Replace with role ID
        'ping_role': 123456789012345678,      # Replace with ping role/user ID
        'panel_name': 'Final Exam',
        'panel_desc': (
            "Please click the button below to start the Final Exam.\n\n"
            "**Requirements:**\n"
            "- You must be CO II\n"
            "- You must be capable to answer questions\n"
            "- You may not use AI\n\n"
            "Good luck!"
        ),
        'input_type': 'button'
    }
}

# Global variables from your code
auto_role_enabled = True
role_to_assign = discord.Object(id=AUTOROLE_ROLE_ID)
sleep_mode = True
loaded_cogs = []
bot.uptime = datetime.utcnow()

# Bot check for sleep mode
@bot.check
async def block_commands_in_sleep_mode(ctx):
    if await bot.is_owner(ctx.author):
        return True  # Bot owner can use all commands regardless of sleep mode
    if not sleep_mode:
        return True
    if ctx.command.name == "start":
        return True  # Allow start command for non-owners
    embed = discord.Embed(
        title="Bot is in sleep mode.",
        description="Bot is in sleep mode, all commands are unavailable except for the bot owner. Please contact the bot developer to start it.",
        color=discord.Color.red()
    )
    embed.set_footer(text=f"Command used: {ctx.command.name} | User ID: {ctx.author.id}")
    await ctx.send(embed=embed)
    return False

# Create application panels in panel channels and delete non-pinned messages
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user.name} ({bot.user.id})")
    print(f"Connected to {len(bot.guilds)} guilds")
    print("Bot is ready!")
    try:
        activity = discord.Activity(
            type=discord.ActivityType.playing,
            name="Waiting for developers to start me.."
        )
        await bot.change_presence(status=discord.Status.idle, activity=activity)
        guild = discord.Object(id=GUILD_ID)
        synced = await bot.tree.sync(guild=guild)
        print(f"Synced {len(synced)} command(s) to guild {guild.id}")
    except Exception as e:
        print(f"Failed to sync commands to guild: {e}")

    # Create application panels
    guild = bot.get_guild(GUILD_ID)
    created_panels = set()  # Track created panel channels to avoid duplicates
    for app_type, app_data in APPLICATIONS.items():
        panel_channel = guild.get_channel(app_data['panel_channel'])
        if panel_channel and app_data['panel_channel'] not in created_panels:
            # Delete all non-pinned messages in the channel
            try:
                async for message in panel_channel.history(limit=100):  # Adjust limit if needed
                    if not message.pinned:
                        await message.delete()
            except discord.Forbidden:
                print(f"Cannot delete messages in channel {panel_channel.name} due to missing permissions.")
            except discord.HTTPException as e:
                print(f"Failed to delete messages in channel {panel_channel.name}: {e}")

            # Create panel embed
            embed = discord.Embed(
                title=app_data.get('panel_name', 'Application Panel'),
                description=(
                    app_data.get('panel_desc', 'Please select an application to start.') if app_type not in ['gang_unit', 'swat_entry', 'internal_affairs', 'field_training']
                    else (
                        "Please select an application in the dropdown below to start the application.\n\n"
                        "**Requirements:**\n"
                        "- You must be 14 or older\n"
                        "- You must have a decent SPaG\n"
                        "- You must use common sense\n"
                        "- You must be dedicated in the division\n"
                        "- You must be capable to answer questions\n"
                        "- You may not use AI\n"
                        "- You must be PO III or higher\n\n"
                        "Good luck!"
                    )
                ),
                color=discord.Color.blue()
            )
            embed.set_footer(text="Los Angeles Police Department")
            view = ApplicationView(app_type)
            try:
                await panel_channel.send(embed=embed, view=view)
                created_panels.add(app_data['panel_channel'])
            except discord.Forbidden:
                print(f"Cannot send panel in channel {panel_channel.name} due to missing permissions.")
            except discord.HTTPException as e:
                print(f"Failed to send panel in channel {panel_channel.name}: {e}")
    print("Application panels created.")

# Button or dropdown for starting an application
class ApplicationView(discord.ui.View):
    def __init__(self, app_type):
        super().__init__(timeout=None)
        self.app_type = app_type
        # Add button or dropdown based on input_type
        if APPLICATIONS[app_type].get('input_type') == 'button':
            self.add_item(discord.ui.Button(
                label="Start Application",
                style=discord.ButtonStyle.green,
                custom_id=f"apply_{app_type}"
            ))
        elif app_type in ['gang_unit', 'swat_entry', 'internal_affairs', 'field_training']:
            options = [
                discord.SelectOption(label=APPLICATIONS[atype]['dropdown_label'], value=atype)
                for atype in APPLICATIONS
                if APPLICATIONS[atype]['panel_channel'] == SHARED_PANEL_CHANNEL
            ]
            select = discord.ui.Select(placeholder="Select an application", options=options, custom_id="subdivision_select")
            select.callback = self.select_callback
            self.add_item(select)

    async def select_callback(self, interaction: discord.Interaction):
        selected_app_type = interaction.data['values'][0]
        user = interaction.user
        await interaction.response.send_message(
            f"Please check your DMs to start the {APPLICATIONS[selected_app_type]['name']} application!",
            ephemeral=True
        )
        try:
            await user.send(f"Starting your {APPLICATIONS[selected_app_type]['name']} application. Please answer the following questions:")
            responses = await collect_application_responses(user, selected_app_type)
            if responses:
                await submit_application(user, selected_app_type, responses)
        except discord.Forbidden:
            await interaction.followup.send("I cannot send you DMs. Please enable DMs from server members.", ephemeral=True)

# Handle button clicks
@bot.event
async def on_interaction(interaction: discord.Interaction):
    if interaction.type == discord.InteractionType.component and interaction.data['custom_id'].startswith('apply_'):
        app_type = interaction.data['custom_id'].split('_')[1]
        user = interaction.user
        await interaction.response.send_message(
            f"Please check your DMs to start the {APPLICATIONS[app_type]['name']} application!",
            ephemeral=True
        )
        try:
            await user.send(f"Starting your {APPLICATIONS[app_type]['name']} application. Please answer the following questions:")
            responses = await collect_application_responses(user, app_type)
            if responses:
                await submit_application(user, app_type, responses)
        except discord.Forbidden:
            await interaction.followup.send("I cannot send you DMs. Please enable DMs from server members.", ephemeral=True)

# Collect application responses in DMs
async def collect_application_responses(user, app_type):
    responses = []
    for question in APPLICATIONS[app_type]['questions']:
        embed = discord.Embed(
            title=f"{APPLICATIONS[app_type]['name']} Application",
            description=question,
            color=discord.Color.blue()
        )
        embed.set_footer(text="Los Angeles Police Department")
        await user.send(embed=embed)
        
        def check(m):
            return m.author == user and isinstance(m.channel, discord.DMChannel)
        
        try:
            response = await bot.wait_for('message', check=check, timeout=600)  # 10-minute timeout
            responses.append(response.content)
        except asyncio.TimeoutError:
            await user.send("You took too long to respond. Application cancelled.")
            return None
    return responses

# Submit application to review channel
async def submit_application(user, app_type, responses):
    guild = bot.get_guild(GUILD_ID)
    review_channel = guild.get_channel(APPLICATIONS[app_type]['review_channel'])
    ping_role = guild.get_role(APPLICATIONS[app_type]['ping_role']) or guild.get_member(APPLICATIONS[app_type]['ping_role'])
    
    embed = discord.Embed(
        title=f"{user.name}'s {APPLICATIONS[app_type]['name']} Application Submission",
        description=f"Here is {user.mention}'s {APPLICATIONS[app_type]['name']} application submission, please use the buttons below.",
        color=discord.Color.blue()
    )
    embed.add_field(name="UserID", value=user.id, inline=True)
    embed.add_field(name="Username", value=user.name, inline=True)
    embed.add_field(name="Joined Guild", value=user.joined_at.strftime('%Y-%m-%d %H:%M:%S') if user.joined_at else "Unknown", inline=True)
    embed.add_field(name="Highest Role", value=user.top_role.mention if user.top_role else "None", inline=True)
    
    for i, (question, answer) in enumerate(zip(APPLICATIONS[app_type]['questions'], responses), 1):
        embed.add_field(name=f"Question {i}: {question}", value=answer, inline=False)
    
    embed.set_footer(text="Los Angeles Police Department")
    
    view = ReviewView(user, app_type)
    ping = ping_role.mention if ping_role else "Reviewers"
    await review_channel.send(content=ping, embed=embed, view=view)
    await user.send(f"Your {APPLICATIONS[app_type]['name']} application has been submitted for review!")

# Review buttons
class ReviewView(discord.ui.View):
    def __init__(self, applicant, app_type):
        super().__init__(timeout=None)
        self.applicant = applicant
        self.app_type = app_type

    @discord.ui.button(label="Accept", style=discord.ButtonStyle.green, custom_id="accept_button")
    async def accept_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.process_review(interaction, True, False)

    @discord.ui.button(label="Accept with Reason", style=discord.ButtonStyle.green, custom_id="accept_reason_button")
    async def accept_reason_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.process_review(interaction, True, True)

    @discord.ui.button(label="Deny", style=discord.ButtonStyle.red, custom_id="deny_button")
    async def deny_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.process_review(interaction, False, False)

    @discord.ui.button(label="Deny with Reason", style=discord.ButtonStyle.red, custom_id="deny_reason_button")
    async def deny_reason_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.process_review(interaction, False, True)

    async def process_review(self, interaction: discord.Interaction, accepted: bool, with_reason: bool):
        reviewer = interaction.user
        guild = bot.get_guild(GUILD_ID)
        applicant_member = guild.get_member(self.applicant.id)
        app_name = APPLICATIONS[self.app_type]['name']
        
        reason = None
        if with_reason:
            modal = ReasonModal()
            await interaction.response.send_modal(modal)
            await modal.wait()
            reason = modal.reason.value if modal.reason.value else "No reason provided."

        # Update embed
        embed = interaction.message.embeds[0]
        embed.color = discord.Color.green() if accepted else discord.Color.red()
        embed.set_footer(text=f"Reviewed by {reviewer.name} | Los Angeles Police Department")
        if reason:
            embed.add_field(name="Review Reason", value=reason, inline=False)
        
        await interaction.message.edit(embed=embed, view=None)
        
        # Notify applicant
        result_embed = discord.Embed(
            title=f"{app_name} Application Result",
            description=f"Your {app_name} application has been {'accepted' if accepted else 'denied'} by {reviewer.mention}.",
            color=discord.Color.green() if accepted else discord.Color.red()
        )
        if reason:
            result_embed.add_field(name="Reason", value=reason, inline=False)
        result_embed.set_footer(text="Los Angeles Police Department")
        
        try:
            await self.applicant.send(embed=result_embed)
        except discord.Forbidden:
            await interaction.followup.send(f"Could not DM {self.applicant.mention} the result.", ephemeral=True)
        
        # Assign role if accepted
        if accepted and applicant_member:
            role = guild.get_role(APPLICATIONS[self.app_type]['role_id'])
            if role:
                await applicant_member.add_roles(role)
        
        # Notify channel
        await interaction.channel.send(
            f"{self.applicant.mention}'s {app_name} application has been {'accepted' if accepted else 'denied'} by {reviewer.mention}."
        )

# Modal for reason input
class ReasonModal(discord.ui.Modal, title="Provide Reason"):
    reason = discord.ui.TextInput(
        label="Reason",
        style=discord.TextStyle.paragraph,
        placeholder="Enter the reason for your decision...",
        required=False,
        max_length=1000
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer()
        self.stop()

# Existing commands from your code
@bot.command()
async def say(ctx, *, message: str):
    allowed_user_id = 1335497299773620287
    banned_user_id = 1030197824702398547
    
    if ctx.author.id == banned_user_id:
        embed = discord.Embed(
            title="UNAUTHORIZED",
            description=f"Hello <@{banned_user_id}>, you have been banned from using this command, and dont you dare ping and beg me again to unban./n **Reason** Self Explanatory : 'There are only 2 genders, Men and woman, *cry about it*'",
            colour=discord.Color.red()
        )
        embed.set_footer(text="Los Angeles Police Department")
        await ctx.send(embed=embed)
        return
    
    if ctx.author.id == allowed_user_id or any(role.id in HR_ROLE_IDS for role in ctx.author.roles):
        try:
            await ctx.message.delete()
            await ctx.send(message)
        except discord.Forbidden:
            await ctx.send("❌ I don't have permission to delete messages.", delete_after=5)
    else:
        await ctx.send("❌ You don't have the required role or permission to use this command.", delete_after=5)

@bot.command(name="announce")
async def announce(ctx, *, message: str):
    if not any(role.id in ALLOWED_ROLE_IDS for role in ctx.author.roles):
        try:
            await ctx.message.delete()
            await ctx.author.send("This is a restricted command, only Bot Tamers and Board of Chiefs members can use it.")
        except discord.Forbidden:
            pass
        return

    try:
        await ctx.message.delete()
    except discord.Forbidden:
        pass

    channel = bot.get_channel(ANNOUNCEMENT_CHANNEL_ID)
    if channel is None:
        await ctx.author.send(f"❌ Announcement channel with ID {ANNOUNCEMENT_CHANNEL_ID} not found.")
        return

    try:
        await channel.send(message)
        await ctx.author.send(f"✅ Announcement sent to {channel.mention}.")
    except discord.Forbidden:
        await ctx.author.send(f"❌ I don't have permission to send messages in {channel.mention}.")

@bot.event
async def on_member_join(member: discord.Member):
    global auto_role_enabled, role_to_assign
    if auto_role_enabled and role_to_assign:
        try:
            role = member.guild.get_role(AUTOROLE_ROLE_ID)
            if role:
                await member.add_roles(role)
                print(f"✅ Assigned {role.name} to {member.name}.")
            else:
                print(f"❌ Role with ID {AUTOROLE_ROLE_ID} not found.")
        except discord.Forbidden:
            print(f"❌ Failed to assign {role.name} to {member.name}. Bot lacks permissions.")
        except discord.HTTPException as e:
            print(f"❌ Failed to assign role: {e}")

@bot.command()
async def test(ctx):
    print("Command executed once")
    await ctx.send("Test command executed.")

@bot.command()
async def dumb(ctx):
    await ctx.send("<@1320762191661764689> shush")
    await ctx.send("<@1320762191661764689> erm why u so dumb")
    await ctx.send("<@1320762191661764689> erm")

@bot.command(name='purge')
@commands.has_permissions(manage_messages=True)
@commands.bot_has_permissions(manage_messages=True)
async def purge(ctx, amount: int):
    if amount < 1 or amount > 100:
        await ctx.send("Please specify a number between 1 and 100.", delete_after=5)
        return
    try:
        await ctx.channel.purge(
            limit=amount + 1,
            check=lambda m: not m.pinned
        )
        await ctx.send(f"Successfully deleted {amount} non-pinned message(s).", delete_after=5)
    except discord.Forbidden:
        await ctx.send("❌ I don't have permission to delete messages.", delete_after=5)
    except discord.HTTPException as e:
        await ctx.send(f"❌ Failed to purge messages: {e}", delete_after=5)

@purge.error
async def purge_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("You need 'Manage Messages' permission.", delete_after=5)
    elif isinstance(error, commands.BotMissingPermissions):
        await ctx.send("I need 'Manage Messages' permission.", delete_after=5)
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("Please specify the number of messages to purge.", delete_after=5)
    elif isinstance(error, commands.CheckFailure):
        return  # Handled by globally_block_banned_users or sleep mode check
    else:
        print(f"Purge error: {error}")
        await ctx.send(f"Error: {str(error)}", delete_after=5)

@bot.command()
async def hello(ctx):
    await ctx.send("You thought I would say hello didn't you, bitch?")

@bot.command()
async def autorole(ctx, status: str, role: discord.Role = None):
    global auto_role_enabled, role_to_assign
    if status.lower() == "on":
        if role:
            role_to_assign = role
            auto_role_enabled = True
            await ctx.send(f"✅ Auto-role is now **ON**. The role {role.mention} will be assigned to all new members.")
        else:
            await ctx.send("❌ You must **mention** a role (e.g., `!autorole on @Role`).")
    elif status.lower() == "off":
        auto_role_enabled = False
        role_to_assign = None
        await ctx.send("🚫 Auto-role is now **OFF**.")
    else:
        await ctx.send("❌ Please specify either `on` or `off`.")

@bot.command()
async def currentautorole(ctx):
    global auto_role_enabled, role_to_assign
    if auto_role_enabled and role_to_assign:
        role = ctx.guild.get_role(AUTOROLE_ROLE_ID)
        await ctx.send(f"✅ Auto-role is **ON**. The assigned role is {role.mention}.")
    else:
        await ctx.send("🚫 Auto-role is **OFF**.")

@bot.command()
async def nick(ctx, member: discord.Member, *, nickname: str = None):
    try:
        await ctx.message.delete()
        old_nick = member.nick or member.name
        await member.edit(nick=nickname)
        if nickname:
            await ctx.send(f"✅ Changed {member.mention}'s nickname from '{old_nick}' to '{nickname}'.")
        else:
            await ctx.send(f"✅ Reset {member.mention}'s nickname to default.")
    except discord.Forbidden:
        await ctx.send("❌ I don't have permission to change this member's nickname.", delete_after=5)
    except discord.HTTPException as e:
        await ctx.send(f"❌ Failed to change nickname: {e}", delete_after=5)

@bot.command()
@commands.is_owner()
async def stop(ctx):
    global sleep_mode
    try:
        activity = discord.Activity(
            type=discord.ActivityType.playing,
            name="Waiting for developers to start me.."
        )
        await bot.change_presence(status=discord.Status.idle, activity=activity)
        sleep_mode = True
        embed = discord.Embed(
            title="Bot Entering Sleep Mode",
            description="The bot is now in sleep mode. All commands are disabled except for the bot owner.",
            color=discord.Color.red(),
            timestamp=datetime.utcnow()
        )
        cogs_list = loaded_cogs if loaded_cogs else ["None"]
        embed.add_field(
            name="Disabled Cogs",
            value=", ".join(cogs_list),
            inline=False
        )
        embed.set_footer(text=f"Command used: stop | User ID: {ctx.author.id}")
        await ctx.send(embed=embed)
    except Exception as e:
        await ctx.send(f"Error setting sleep mode: {e}")

@bot.command()
@commands.is_owner()
async def start(ctx):
    global sleep_mode
    try:
        activity = discord.Activity(
            type=discord.ActivityType.watching,
            name="Los Angeles Police Department"
        )
        await bot.change_presence(status=discord.Status.dnd, activity=activity)
        sleep_mode = False
        embed = discord.Embed(
            title="Bot Activated",
            description="The bot is now active and all commands are available.",
            color=discord.Color.green(),
            timestamp=datetime.utcnow()
        )
        cogs_list = loaded_cogs if loaded_cogs else ["None"]
        embed.add_field(
            name="Enabled Cogs",
            value=", ".join(cogs_list),
            inline=False
        )
        embed.set_footer(text=f"Command used: start | User ID: {ctx.author.id}")
        await ctx.send(embed=embed)
    except Exception as e:
        await ctx.send(f"Error activating bot: {e}")

# Load cogs
async def load_extensions():
    global loaded_cogs
    cogs = [
        "cogs.jishaku",
        "cogs.trainingevents",
        "cogs.support",
        "cogs.lapd",
        "cogs.embedbuilder",
        "cogs.panel",
        "cogs.certification_requests",
        "cogs.shift",
        "cogs.assignto"
    ]
    for cog in cogs:
        try:
            await bot.load_extension(cog)
            print(f"Loaded {cog} cog")
            loaded_cogs.append(cog.split(".")[-1])
        except Exception as e:
            print(f"Failed to load {cog} cog: {e}")

# Main function
async def main():
    await load_extensions()
    keep_alive()
    try:
        await bot.start(BOT_TOKEN)
    except Exception as e:
        print(f"Failed to start bot: {e}")

if __name__ == "__main__":
    asyncio.run(main())