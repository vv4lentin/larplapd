import discord
from discord import Embed, Colour, ButtonStyle, Interaction, Member, Permissions
from discord.ui import Button, View
from discord.ext import commands

class CancelButton(View):
    def __init__(self, host: str, original_message_id: int, event_type: str):
        super().__init__(timeout=None)  # Persistent view
        self.host = host
        self.original_message_id = original_message_id
        self.event_type = event_type  # To differentiate between Training and Orientation

    @discord.ui.button(label="Cancel", style=ButtonStyle.red)
    async def cancel_button(self, interaction: Interaction, button: Button):
        if interaction.user.display_name != self.host:
            await interaction.response.send_message(f"Only the host can cancel this {self.event_type.lower()}!", ephemeral=True)
            return
        
        # Reply to the original message
        await interaction.response.send_message(content=f"{self.event_type} cancelled.", reply_to=self.original_message_id)
        # Disable the button after use
        button.disabled = True
        await interaction.message.edit(view=self)

class TrainingEvents(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="training", description="Announces a training in the specified channel.")
    async def training(self, ctx: commands.Context, host: str, when: str, location: str, servercode: str, cohost: str = None, notes: str = None):
        # Define the target channel
        channel = self.bot.get_channel(1329908997381296220)
        if not channel:
            await ctx.send("Error: Target channel not found.", delete_after=10)
            return

        # Create the embed
        embed = Embed(
            title="LAPD • Training Announcement",
            description="React if attending ✅",
            colour=Colour.blue()
        )
        embed.add_field(name="Host", value=host, inline=False)
        embed.add_field(name="Co-Host / Helpers", value=cohost if cohost else "N/A", inline=False)
        embed.add_field(name="When", value=when, inline=False)
        embed.add_field(name="Location", value=location, inline=False)
        embed.add_field(name="Server code", value=servercode, inline=False)
        embed.add_field(name="Notes", value=notes if notes else "N/A", inline=False)
        embed.set_footer(text=f"Sent by {ctx.author.display_name}")

        # Create the view with the Cancel button
        view = CancelButton(host=host, original_message_id=None, event_type="Training")

        # Send the ping message
        await channel.send(content="<@&1306380788056723578> <@&1306380827143180340>")

        # Send the embed with the button
        message = await channel.send(embed=embed, view=view)

        # Update the view with the message ID for replying
        view.original_message_id = message.id
        await message.edit(view=view)

        # Add the ✅ reaction
        await message.add_reaction("✅")

        # Confirm command execution
        await ctx.send("Training announcement sent successfully!", delete_after=10)

    @commands.command(name="orientation", description="Announces an orientation in the specified channel.")
    async def orientation(self, ctx: commands.Context, host: str, when: str, location: str, servercode: str, cohost: str = None, notes: str = None):
        # Define the target channel
        channel = self.bot.get_channel(1329908997381296220)
        if not channel:
            await ctx.send("Error: Target channel not found.", delete_after=10)
            return

        # Create the embed
        embed = Embed(
            title="LAPD • Orientation Announcement",
            description="React if attending ✅",
            colour=Colour.blue()
        )
        embed.add_field(name="Host", value=host, inline=False)
        embed.add_field(name="Co-Host / Helpers", value=cohost if cohost else "N/A", inline=False)
        embed.add_field(name="When", value=when, inline=False)
        embed.add_field(name="Location", value=location, inline=False)
        embed.add_field(name="Server code", value=servercode, inline=False)
        embed.add_field(name="Notes", value=notes if notes else "N/A", inline=False)
        embed.set_footer(text=f"Sent by {ctx.author.display_name}")

        # Create the view with the Cancel button
        view = CancelButton(host=host, original_message_id=None, event_type="Orientation")

        # Send the ping message
        await channel.send(content="<@&1306380788056723578> <@&1306380858437144576>")

        # Send the embed with the button
        message = await channel.send(embed=embed, view=view)

        # Update the view with the message ID for replying
        view.original_message_id = message.id
        await message.edit(view=view)

        # Add the ✅ reaction
        await message.add_reaction("✅")

        # Confirm command execution
        await ctx.send("Orientation announcement sent successfully!", delete_after=10)

    @commands.command(name="logorientation", description="Logs the result of an orientation in the specified channel.")
    async def logorientation(self, ctx: commands.Context, host: str, trainee: Member, result: str, comments: str, cohost: str = None):
        # Define the target channel
        channel = self.bot.get_channel(1328036335826763939)
        if not channel:
            await ctx.send("Error: Target channel not found.", delete_after=10)
            return

        # Check if trainee is provided and valid
        if not trainee:
            await ctx.send("Error: A valid trainee must be provided.", delete_after=10)
            return

        # Add the role to the trainee
        role = ctx.guild.get_role(1306380827143180340)
        if not role:
            await ctx.send("Error: Target role not found.", delete_after=10)
            return

        try:
            await trainee.add_roles(role)
        except Exception as e:
            await ctx.send(f"Error: Failed to add role to trainee. {str(e)}", delete_after=10)
            return

        # Create the embed
        embed = Embed(
            title="Orientation • Result",
            colour=Colour.blue()
        )
        embed.add_field(name="Host", value=host, inline=False)
        embed.add_field(name="Co-Hosts", value=cohost if cohost else "N/A", inline=False)
        embed.add_field(name="Trainee", value=trainee.mention, inline=False)
        embed.add_field(name="Result", value=result if result else "N/A", inline=False)
        embed.add_field(name="Comments", value=comments if comments else "N/A", inline=False)
        embed.set_footer(text=f"Issued by {ctx.author.display_name}")

        # Send the trainee ping and embed
        await channel.send(content=trainee.mention, embed=embed)

        # Confirm command execution
        await ctx.send("Orientation result logged successfully!", delete_after=10)

    @commands.command(name="logtraining", description="Logs the result of a training in the specified channel.")
    async def logtraining(self, ctx: commands.Context, host: str, trainee: Member, result: str, comments: str, cohost: str = None):
        # Define the target channel
        channel = self.bot.get_channel(1329939121086529566)
        if not channel:
            await ctx.send("Error: Target channel not found.", delete_after=10)
            return

        # Check if trainee is provided and valid
        if not trainee:
            await ctx.send("Error: A valid trainee must be provided.", delete_after=10)
            return

        # Add the role to the trainee
        role = ctx.guild.get_role(1306380805752361020)
        if not role:
            await ctx.send("Error: Target role not found.", delete_after=10)
            return

        try:
            await trainee.add_roles(role)
        except Exception as e:
            await ctx.send(f"Error: Failed to add role to trainee. {str(e)}", delete_after=10)
            return

        # Create the embed
        embed = Embed(
            title="Training • Result",
            description=f"{trainee.mention} Please take your final exam.",
            colour=Colour.blue()
        )
        embed.add_field(name="Host", value=host, inline=False)
        embed.add_field(name="Co-Hosts", value=cohost if cohost else "N/A", inline=False)
        embed.add_field(name="Trainee", value=trainee.mention, inline=False)
        embed.add_field(name="Result", value=result if result else "N/A", inline=False)
        embed.add_field(name="Comments", value=comments if comments else "N/A", inline=False)
        embed.set_footer(text=f"Issued by {ctx.author.display_name}")

        # Send the trainee ping and embed
        await channel.send(content=trainee.mention, embed=embed)

        # Confirm command execution
        await ctx.send("Training result logged successfully!", delete_after=10)

    @commands.command(name="massshift", description="Announces a mass shift in the specified channel.")
    async def massshift(self, ctx: commands.Context, host: str):
        # Define the target channel
        channel = self.bot.get_channel(1292541172807635066)
        if not channel:
            await ctx.send("Error: Target channel not found.", delete_after=10)
            return

        # Send the message
        message = await channel.send(
            content=f"||<@&1292541838904791040>||\n{host} is hosting a **MASS SHIFT**.\n3+ votes required to start\nReact if attending ✅"
        )

        # Add the ✅ reaction
        await message.add_reaction("✅")

        # Confirm command execution
        await ctx.send("Mass shift announcement sent successfully!", delete_after=10)

    @commands.command(name="logmassshift", description="Logs the result of a mass shift in the specified channel.")
    async def logmassshift(self, ctx: commands.Context, host: str, started: str, ended: str, attendedusers: str, promotedusers: str, cohost: str = None):
        # Define the target channel
        channel = self.bot.get_channel(1328036189973909655)
        if not channel:
            await ctx.send("Error: Target channel not found.", delete_after=10)
            return

        # Create the embed
        embed = Embed(
            title="LAPD • Mass Shift",
            colour=Colour.blue()
        )
        embed.add_field(name="Host", value=host, inline=False)
        embed.add_field(name="Co-Hosts", value=cohost if cohost else "N/A", inline=False)
        embed.add_field(name="Started at", value=started if started else "N/A", inline=False)
        embed.add_field(name="Ended at", value=ended if ended else "N/A", inline=False)
        embed.add_field(name="Attended users", value=attendedusers if attendedusers else "N/A", inline=False)
        embed.add_field(name="Promoted users", value=promotedusers if promotedusers else "N/A", inline=False)
        embed.set_footer(text=f"Issued by {ctx.author.display_name}")

        # Send the embed
        await channel.send(embed=embed)

        # Confirm command execution
        await ctx.send("Mass shift result logged successfully!", delete_after=10)

    @commands.command(name="sync", description="Syncs slash commands for the specified guild.")
    @commands.has_permissions(administrator=True)
    async def sync(self, ctx: commands.Context):
        # Check if the command is run in the correct guild
        if str(ctx.guild.id) != "1292523481539543193":
            await ctx.send("Error: This command can only be used in the specified guild.", delete_after=10)
            return

        try:
            # Sync commands for the specific guild
            synced = await self.bot.tree.sync(guild=discord.Object(id=1292523481539543193))
            await ctx.send(f"Successfully synced {len(synced)} commands for the guild!", delete_after=10)
        except Exception as e:
            await ctx.send(f"Error: Failed to sync commands. {str(e)}", delete_after=10)

async def setup(bot):
    await bot.add_cog(TrainingEvents(bot))
