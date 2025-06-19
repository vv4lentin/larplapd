import discord
from discord.ext import commands
import random

class AssignTO(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='assignto')
    async def assign_to(self, ctx):
        # Define role and channel IDs
        prob_officer_role_id = 1306380788056723578
        to_role_id = 1306458665410236436
        target_channel_id = 1292569010407346257

        # Get the guild and target channel
        guild = ctx.guild
        target_channel = guild.get_channel(target_channel_id)

        if not target_channel:
            await ctx.send("Error: Target channel not found.")
            return

        # Get members with the specified roles
        prob_officers = [member for member in guild.members if prob_officer_role_id in [role.id for role in member.roles]]
        tos = [member for member in guild.members if to_role_id in [role.id for role in member.roles]]

        if not prob_officers:
            await ctx.send("Error: No Probationary Officers found.")
            return
        if not tos:
            await ctx.send("Error: No TOs found.")
            return

        # Create assignments
        assignments = []
        for prob_officer in prob_officers:
            assigned_to = random.choice(tos)
            assignments.append(f"{prob_officer.mention} -> {assigned_to.mention}")

        # Create the embed
        embed = discord.Embed(
            title="TOs & Probationary Officers Assignation",
            description="Here is the list of all Probationary Officers with their assigned TOs.",
            color=discord.Color.blue()
        )

        # Split assignments into fields to avoid exceeding 1024 characters
        if assignments:
            current_field = ""
            field_count = 1

            for assignment in assignments:
                # Check if adding the next assignment would exceed 1024 characters
                if len(current_field) + len(assignment) + 1 <= 1024:
                    current_field += assignment + "\n"
                else:
                    # Add the current field to the embed
                    embed.add_field(
                        name=f"Assignments (Part {field_count})" if field_count > 1 else "Assignments",
                        value=current_field.strip() or "No assignments in this part.",
                        inline=False
                    )
                    # Start a new field
                    current_field = assignment + "\n"
                    field_count += 1

            # Add the last field if it contains any assignments
            if current_field:
                embed.add_field(
                    name=f"Assignments (Part {field_count})" if field_count > 1 else "Assignments",
                    value=current_field.strip(),
                    inline=False
                )
        else:
            embed.add_field(
                name="Assignments",
                value="No assignments could be made.",
                inline=False
            )

        # Send the embed to the target channel
        try:
            await target_channel.send(embed=embed)
            await ctx.send(f"Assignments have been posted in {target_channel.mention}.")
        except discord.HTTPException as e:
            await ctx.send(f"Error sending embed: {e}")

async def setup(bot):
    await bot.add_cog(AssignTO(bot))
