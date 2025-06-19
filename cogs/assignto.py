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

        # Create assignments: Distribute Probationary Officers among TOs
        assignments = {to: [] for to in tos}  # Dictionary to store TO -> List of Prob Officers
        prob_officers_copy = prob_officers.copy()  # Copy to manipulate
        random.shuffle(prob_officers_copy)  # Shuffle for random distribution

        # Distribute Probationary Officers as evenly as possible
        while prob_officers_copy:
            for to in tos:
                if prob_officers_copy:
                    assignments[to].append(prob_officers_copy.pop())

        # Create the embed
        embed = discord.Embed(
            title="TOs & Probationary Officers Assignation",
            description="Here is the list of all Probationary Officers with their assigned TOs.",
            color=discord.Color.blue()
        )

        # Add fields for each TO
        for to, assigned_probs in assignments.items():
            if assigned_probs:  # Only add a field if the TO has assigned officers
                # Create the field content
                field_value = "\n".join(f"- {prob.mention}" for prob in assigned_probs)
                # Ensure field value is under 1024 characters
                if len(field_value) > 1024:
                    field_value = field_value[:1000] + "... (truncated)"
                embed.add_field(
                    name=f"{to.display_name} ({to.mention})",
                    value=field_value or "No Probationary Officers assigned.",
                    inline=False
                )
            else:
                embed.add_field(
                    name=f"{to.display_name} ({to.mention})",
                    value="No Probationary Officers assigned.",
                    inline=False
                )

        # If no assignments were made (edge case)
        if not any(assignments.values()):
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
