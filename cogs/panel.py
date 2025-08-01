import discord
from discord.ext import commands
from discord.ui import Button, View, Modal, TextInput
from discord import Interaction, TextStyle
from datetime import datetime
import re

# Simulated callsign storage (replace with database if needed)
callsigns_db = {}  # Format: {user_id: callsign}

# Callsign Request Modal
class CallsignModal(discord.ui.Modal, title="Request a Callsign"):
    def __init__(self):
        super().__init__()
        self.roblox_discord = discord.ui.TextInput(
            label="Roblox + Discord User",
            placeholder="Enter your Roblox and Discord username",
            required=True
        )
        self.callsign = discord.ui.TextInput(
            label="Callsign Requested",
            placeholder="Enter the callsign you want",
            required=True
        )
        self.add_item(self.roblox_discord)
        self.add_item(self.callsign)

    async def on_submit(self, interaction: Interaction):
        # Create embed for callsign request
        embed = discord.Embed(
            title="Callsign Request",
            color=discord.Color.blue(),
            timestamp=datetime.now()
        )
        embed.add_field(name="Who", value=interaction.user.mention, inline=False)
        embed.add_field(name="Callsign", value=self.callsign.value, inline=False)

        # Create accept/deny buttons
        view = View(timeout=None)
        accept_button = Button(label="Accept", style=discord.ButtonStyle.green, custom_id=f"accept_callsign_{interaction.user.id}_{self.callsign.value}")
        deny_button = Button(label="Deny", style=discord.ButtonStyle.red, custom_id=f"deny_callsign_{interaction.user.id}")

        async def accept_callback(interaction: Interaction):
            # Extract requester's user ID from custom_id
            requester_id = int(interaction.data['custom_id'].split('_')[2])
            callsign = interaction.data['custom_id'].split('_')[3]
            # Store callsign for requester (replace with database logic)
            callsigns_db[requester_id] = callsign
            await interaction.response.send_message(f"Callsign `{callsign}` approved for <@{requester_id}>!", ephemeral=True)
            # Disable buttons after action
            accept_button.disabled = True
            deny_button.disabled = True
            await interaction.message.edit(view=view)

        async def deny_callback(interaction: Interaction):
            requester_id = int(interaction.data['custom_id'].split('_')[2])
            await interaction.response.send_message(f"Callsign request for <@{requester_id}> denied.", ephemeral=True)
            # Disable buttons after action
            accept_button.disabled = True
            deny_button.disabled = True
            await interaction.message.edit(view=view)

        accept_button.callback = accept_callback
        deny_button.callback = deny_callback
        view.add_item(accept_button)
        view.add_item(deny_button)

        # Send request to specified channel
        channel = interaction.guild.get_channel(1353106180406509682)
        if channel:
            await channel.send(embed=embed, view=view)
            await interaction.response.send_message("Callsign request submitted!", ephemeral=True)
        else:
            await interaction.response.send_message("Error: Request channel not found.", ephemeral=True)

# Arrest Modal (unchanged)
class ArrestModal(discord.ui.Modal, title="Log an Arrest"):
    def __init__(self):
        super().__init__()
        self.suspect = discord.ui.TextInput(
            label="Suspect",
            placeholder="Enter suspect(s) name",
            required=True
        )
        self.charges = discord.ui.TextInput(
            label="Charges",
            placeholder="List the charges",
            required=True,
            style=discord.TextStyle.paragraph
        )
        self.primary_officer = discord.ui.TextInput(
            label="Primary Officer",
            placeholder="Enter primary officer name",
            required=True
        )
        self.other_officers = discord.ui.TextInput(
            label="Secondary and Tertiary Officers",
            placeholder="Enter other officers names and their callsign or N/A",
            required=False
        )
        self.notes = discord.ui.TextInput(
            label="Notes",
            placeholder="Additional notes (optional)",
            required=False,
            style=discord.TextStyle.paragraph
        )
        self.add_item(self.suspect)
        self.add_item(self.charges)
        self.add_item(self.primary_officer)
        self.add_item(self.other_officers)
        self.add_item(self.notes)

    async def on_submit(self, interaction: Interaction):
        embed = discord.Embed(
            title="New Arrest Log",
            description="Please send the mugshot!",
            color=discord.Color.green(),
            timestamp=datetime.now()
        )
        embed.add_field(name="Suspect", value=self.suspect.value, inline=False)
        embed.add_field(name="Crimes", value=self.charges.value, inline=False)
        embed.add_field(name="Primary Officer", value=self.primary_officer.value, inline=False)
        embed.add_field(name="Secondary and Tertiary Officers", value=self.other_officers.value or "None", inline=False)
        embed.add_field(name="Notes", value=self.notes.value or "None", inline=False)
        await interaction.response.send_message(embed=embed)

# Panel Cog
class Panel(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Define the punishment roles
        self.punishment_roles = [
            1306382455044964415,  # Punishment Role 1
            1306382453283225650,  # Punishment Role 2
            1306382451228016660,  # Punishment Role 3
            1306382449378594867,  # Punishment Role 4
            1324540074834133033,  # Punishment Role 5
            1324540189594353787   # Punishment Role 6
        ]
        self.required_role_id = 1292541838904791040  # Role ID to check

    @commands.command(name="panel")
    async def panel(self, ctx):
        # Create the embed for the panel
        embed = discord.Embed(
            title="Welcome to Your Panel",
            description="Below you can see buttons for the following options.",
            color=discord.Color.blue()
        )
        embed.add_field(
            name="📝 Log Arrest",
            value="Use this to Log an Arrest.",
            inline=False
        )
        embed.add_field(
            name="👮 View Punishments",
            value="Use this to view your active Punishments.",
            inline=False
        )
        embed.add_field(
            name="📢 Request Callsign",
            value="Use this to request a callsign.",
            inline=False
        )
        embed.set_thumbnail(url="https://upload.wikimedia.org/wikipedia/commons/thumb/5/497/Los_Angeles_Police_Department_seal.svg/512px-Los_Angeles_Police_Department_seal.svg.png")
        embed.set_image(url="https://cdn.discordapp.com/attachments/1369422640003153961/1377358249044742174/Los_Angeles_Police_Department_1_1.png?ex=6838ac54&is=68375ad4&hm=e2dde275075c243188d3f18f71a984b486672877fff44ded4ae4baff3ca821fd&")

        # Create the buttons
        view = View(timeout=None)  # Persistent view

        # Log Arrest Button
        log_arrest_button = Button(label="Log Arrest", style=discord.ButtonStyle.primary, custom_id="log_arrest")
        async def log_arrest_callback(interaction: discord.Interaction):
            modal = ArrestModal()
            await interaction.response.send_modal(modal)
        log_arrest_button.callback = log_arrest_callback

        # View Punishments Button
        view_punishments_button = Button(label="View Punishments", style=discord.ButtonStyle.secondary, custom_id="view_punishments")
        async def view_punishments_callback(interaction: discord.Interaction):
            user = interaction.user
            user_roles = [role.id for role in user.roles]
            active_punishments = [role for role in self.punishment_roles if role in user_roles]
            embed = discord.Embed(
                title=f"Punishments for - {user.display_name} -",
                color=discord.Color.red(),
                timestamp=datetime.now()
            )
            embed.set_thumbnail(url="https://upload.wikimedia.org/wikipedia/commons/thumb/5/497/Los_Angeles_Police_Department_seal.svg/512px-Los_Angeles_Police_Department_seal.svg.png")
            if active_punishments:
                punishment_list = "\n".join([f"<@&{role_id}>" for role_id in active_punishments])
                embed.description = punishment_list
            else:
                embed.description = "No active punishments."
            await interaction.response.send_message(embed=embed, ephemeral=True)
        view_punishments_button.callback = view_punishments_callback

        # Callsign Request Button
        callsign_button = Button(label="Request Callsign", style=discord.ButtonStyle.green, custom_id="request_callsign")
        async def callsign_callback(interaction: discord.Interaction):
            modal = CallsignModal()
            await interaction.response.send_modal(modal)
        callsign_button.callback = callsign_callback

        # Add buttons to the view
        view.add_item(log_arrest_button)
        view.add_item(view_punishments_button)
        view.add_item(callsign_button)

        # Send the embed with the buttons
        await ctx.send(embed=embed, view=view)

    @commands.command(name="callsigns")
    async def callsigns(self, ctx):
        # Create embed for listing callsigns
        embed = discord.Embed(
            title="Callsigns",
            color=discord.Color.blue(),
            timestamp=datetime.now()
        )
        if callsigns_db:
            callsign_list = "\n".join([f"<@{user_id}>: {callsign}" for user_id, callsign in callsigns_db.items()])
            embed.description = callsign_list
        else:
            embed.description = "No callsigns assigned."
        channel = ctx.guild.get_channel(1344921844557414411)
        if channel:
            await channel.send(embed=embed)
        else:
            await ctx.send("Error: Callsign list channel not found.")

    @commands.command(name="nocallsign")
    async def nocallsign(self, ctx):
        # Create embed for members without callsigns
        embed = discord.Embed(
            title="Members Without Callsigns",
            color=discord.Color.red(),
            timestamp=datetime.now()
        )
        role = ctx.guild.get_role(self.required_role_id)
        if not role:
            await ctx.send("Error: Role not found.")
            return
        members_without_callsign = [member.mention for member in role.members if member.id not in callsigns_db]
        if members_without_callsign:
            embed.description = "\n".join(members_without_callsign)
        else:
            embed.description = "All members with this role have callsigns."
        channel = ctx.guild.get_channel(1344921844557414411)
        if channel:
            await channel.send(embed=embed)
        else:
            await ctx.send("Error: Callsign list channel not found.")

    @commands.command(name="copycallsigns")
    async def copycallsigns(self, ctx):
        # Check if the message is a reply
        if not ctx.message.reference:
            await ctx.send("Error: You must reply to a message with a 'Callsigns' embed to use this command.")
            return

        # Fetch the replied-to message
        try:
            replied_message = await ctx.channel.fetch_message(ctx.message.reference.message_id)
        except discord.NotFound:
            await ctx.send("Error: Replied message not found.")
            return

        # Check if the replied message has an embed
        if not replied_message.embeds or not replied_message.embeds[0].title == "Callsigns":
            await ctx.send("Error: Replied message must contain a 'Callsigns' embed.")
            return

        embed = replied_message.embeds[0]
        if not embed.description or embed.description == "No callsigns assigned.":
            await ctx.send("Error: The embed has no callsigns to copy.")
            return

        # Parse the embed description (format: <@user_id>: callsign)
        added_count = 0
        for line in embed.description.split("\n"):
            match = re.match(r"<@(\d+)>: (.+)", line)
            if match:
                user_id = int(match.group(1))
                callsign = match.group(2).strip()
                callsigns_db[user_id] = callsign  # Add to database
                added_count += 1

        await ctx.send(f"Successfully copied {added_count} callsign(s) to the database.")

    async def on_member_update(self, before, after):
        # Check if the required role was removed
        role = after.guild.get_role(self.required_role_id)
        if not role:
            return  # Role not found, exit

        had_role_before = role in before.roles
        has_role_after = role in after.roles

        # If the member lost the role and is in the callsign database, remove them
        if had_role_before and not has_role_after and after.id in callsigns_db:
            del callsigns_db[after.id]

async def setup(bot):
    await bot.add_cog(Panel(bot))
