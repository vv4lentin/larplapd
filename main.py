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
SHARED_PANEL_CHANNEL = 1294756718693060740  # Shared panel channel ID for Sub-Divisions
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
            'What is your Roblox username?',
            'Are you over the age of 13?',
            'How active are you on a scale from 1-10? What experience do you have being a law enforcement officer?',
            'Why do you want to apply to be an officer?',
            'Can you explain the difference between code 3 and 2.',
            'When making a traffic stop the driver gets aggressive and starts to shout. What actions should you take and describe it in detail.',
            'Can you describe in detail what you would do in preparation to responding to a 911 call about a robbery.',
            'Why should I pick this application over the others?',
            'Do you understand you will be given 2 weeks (14 days) to finish your probationary period. If it has not been completed before then you will be made to restart your application.',
            'Do you understand the minimum quota is 2 hours a week and failure to complete the quota will resort in a warning.',
            'Do you understand any disrespect to a higher command officer will not be tolerated and could lead to you being terminated.',
            'Any questions?'
        ],
        'review_channel': 1308254140702392360,
        'panel_channel': 1292534061394558986,
        'role_id': 1306380858437144576,
        'ping_role': 1324522426771443813,
        'panel_name': 'Los Angeles Police Department Entry Application',
        'panel_desc': (
            "Please click the button below to start the application.\n\n"
            "**Requirements:**\n"
            "- You must be 13 or older\n"
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
            'What is your Roblox and Discord username?',
            'What is your LAPD Rank? ',
            'Are you 13 or older? ',
            'Do you have prior experience within the Gang Unit (G.U)?',
            'If someone told you about a gang in the neighborhood, but they had no location what would you do?',
            'What steps would you take to raid a gang house ?',
            'What is the primary Objective of the Gang Unit (G.U) ?',
            'What would your course of action be if you saw a person affiliated with a gang?',
            'Do you agree to obey all commands that are given not only by Gang Unit command. But also LAPD Command? ',
            'Do you have any questions ?'
        ],
        'review_channel': 1399136987658719453,
        'panel_channel': SHARED_PANEL_CHANNEL,
        'role_id': 1379196070328008724,
        'ping_role': 1379193380201959454,
        'dropdown_label': 'Gang Unit Application'
    },
    'metro_entry': {
        'name': 'Metro | Entry',
        'questions': [
            'How old are you?',
            'Why do you want to join the LAPD METRO? (+2 sentences)',
            'What will you bring to the LAPD METRO? (+2 sentences) ',
            'How would you respond to a bank robbery? (+3 sentences) ',
            'Is METRO permitted to patrol?',
            'What would your first instinct be on-scene on at a hostage Scene?  (+3 sentences) ',
            'Do you understand the Laws and Miranda rights?',
            'On a scale of 1-10 how well do you know the 10 codes?',
            'How active will you be on a scale of 1-10?',
            'What would you do during a riot? (+2 sentences)',
            'Do you understand that asking for your application to be read will result in IMMEDIATE denial?',
            'Whats your Roblox Username and Discord Username?'
        ],
        'review_channel': 1404188642620080138,
        'panel_channel': 1404120240689778750,  # Separate Metro panel channel
        'role_id': 1348415029837430956,
        'ping_role': 1348413774528381101,
        'panel_name': 'Metro Application',
        'panel_desc': (
            "Please click the button below to start the application.\n\n"
            "**Requirements:**\n"
            "- You must be 14 or older\n"
            "- You must have a decent SPaG\n"
            "- You must use common sense\n"
            "- You must be dedicated in the division\n"
            "- You must be capable to answer questions\n"
            "- You may not use AI\n"
            "- You must be PO III or higher\n\n"
            "Good luck!"
        ),
        'input_type': 'button'
    },
    'internal_affairs': {
        'name': 'Internal Affairs',
        'questions': [
            'use docs',
            'use docs',
            'use docs or tell farts to send me questions'
        ],
        'review_channel': 1404187400867024997,
        'panel_channel': SHARED_PANEL_CHANNEL,
        'role_id': 1306382068116230264,
        'ping_role': 1306381893515870209,
        'dropdown_label': 'IA Application'
    },
    'field_training': {
        'name': 'Field Training Program',
        'questions': [
            'Why do you want to be a TO or Training Officer? 2+ sentences',
            'What are the primary responsibilities of a Field Training Officer (FTO), specifically within the LAPD?',
            'What would you do in the situation your rookie was getting annoyed with you and started shouting?',
            'What prior experience do you have training or mentoring new recruits in Law enforcement?',
            'How would you ensure new officers understand and follow the departments rules and standard operating procedures?',
            'Can you describe a situation where you had to handle a difficult or inexperienced recruit? How did you manage the situation?',
            'How do you handle a recruit who is not following commands or making consistent mistakes in the field?',
            'Do you understand being a TO comes with a lot of responsibilitys?',
            'Do you understand you will need to put in a minimum of 3 training per week to continue being a TO?',
            'Have you ever had any Internal Affairs cases on you?',
            'Do you understand if you are ever being investigated by IA your placement of a TO will be removed.',
            'What is your rank and do you have any questions?'
        ],
        'review_channel': 1308254092434608168,
        'panel_channel': SHARED_PANEL_CHANNEL,
        'role_id': 1306381034895708193,
        'ping_role': 1306380914732957779,
        'dropdown_label': 'FTO Application'
    },
    'sergeant': {
        'name': 'Sergeant',
        'questions': [
            ' Why do you want to be a police sergeant? ',
            ' What are your strengths and weaknesses? ',
            ' Do you have any aspirations for the academy? ',
            ' What benefical ideas can you bring to both the Los Angeles Dept and the overall academy? ',
            ' Do you understand past sergeant you are a key part to the Department and must always stay professional, failure to do so may demote you back to Police Officer 4 or below ',
            ' With your strenghs in mind, how do they apply to this role? ',
                ' What are key qualities for being a Supervisor/ Sergeant?'
        ],
        'review_channel': 1404187637761179668,
        'panel_channel': 1401639622752338072,
        'role_id': 1306387881803120670,
        'ping_role': 1339058176003407915,
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
            'Explain the Chain of Command and its importance.',
            'What is the process for a Officer to achieve Grappler Certification, and why is this certification significant?',
            'Outline the steps a probationary officer must complete to transition from the Academy to becoming a Patrol Officer?',
            'What role does the FTO program play in shaping new recruits. 2+ sentances.',
            'Describe the procedures that must be taken when performing a traffic stop. 2+ sentences. ',
            'Explain the rule of department personnel adhering to realistic driving practices.',
            'Explain the significance of the Safe Zone rule in maintaining a balanced and fair environment for players, and the exceptions to this rule.',
            'You are driving around and see a Police Officer abusing and cuff rushing. You dont know if hes WL or not. What do you do?',
            'While on patrol, your tires are shot out and two civilians approach your vehicle, carrying firearms. What do you do?',
            'While in a training, you notice a LAPD Officer being very rude to other attendees but the host doesnt seem to care. What do you do?',
            'You are in game and see a LAPD HR leading a group of LAPD around, causing VDM, RDM, and breaking many rules. The moderators are not responding. What do you do?',
            'Do you have any questions?'
            
            
        ],
        'review_channel': 1308254277592154123,
        'panel_channel': 1292816066216591361,
        'role_id': 1306380762542637150,
        'ping_role': 1339058176003407915,
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

# Global variables
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
                description=app_data.get('panel_desc', 'Please select an application to start.'),
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
        elif app_type in ['gang_unit', 'internal_affairs', 'field_training']:
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
        print(f"Dropdown selected: {selected_app_type} by {user.name} ({user.id})")
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
    if interaction.type == discord.InteractionType.component:
        custom_id = interaction.data.get('custom_id', '')
        print(f"Interaction received: custom_id={custom_id}, user={interaction.user.name} ({interaction.user.id})")
        if custom_id.startswith('apply_'):
            app_type = custom_id.split('_')[1]
            if app_type in APPLICATIONS:
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
            else:
                print(f"Invalid app_type: {app_type}")
        elif custom_id == 'subdivision_select':
            # Handled by ApplicationView.select_callback
            pass
        else:
            print(f"Unhandled component interaction: {custom_id}")

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

@bot.command(name='roleall')
@commands.has_permissions(administrator=True)  # Restrict to admins
async def roleall(ctx, role1: discord.Role, role2: discord.Role):
    # Check if the bot has permission to manage roles
    if not ctx.guild.me.guild_permissions.manage_roles:
        await ctx.send("I don't have permission to manage roles!")
        return

    # Check if the bot's highest role is above both role1 and role2
    if ctx.guild.me.top_role <= role1 or ctx.guild.me.top_role <= role2:
        await ctx.send("I can't assign roles higher than or equal to my highest role!")
        return

    # Check if the command issuer's highest role is above both role1 and role2
    if ctx.author.top_role <= role1 or ctx.author.top_role <= role2:
        await ctx.send("You can't manage roles higher than or equal to your highest role!")
        return

    # Get all members with role1
    members_with_role1 = [member for member in ctx.guild.members if role1 in member.roles]

    if not members_with_role1:
        await ctx.send(f"No members have the role {role1.name}.")
        return

    # Assign role2 to members with role1
    success_count = 0
    for member in members_with_role1:
        try:
            await member.add_roles(role2)
            success_count += 1
        except discord.Forbidden:
            await ctx.send(f"Failed to assign {role2.name} to {member.name} due to insufficient permissions.")
            return
        except Exception as e:
            await ctx.send(f"An error occurred while assigning {role2.name} to {member.name}: {e}")
            return

    await ctx.send(f"Successfully assigned {role2.name} to {success_count} member(s) with {role1.name}.")

# Error handling for the command
@roleall.error
async def roleall_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("You need Administrator permissions to use this command!")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("Please provide two roles! Usage: !roleall <role1> <role2>")
    elif isinstance(error, commands.RoleNotFound):
        await ctx.send("One or both roles were not found! Please mention valid roles.")
    else:
        await ctx.send(f"An error occurred: {error}")
        
# Existing commands
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
