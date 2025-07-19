import discord
from discord.ext import commands
import random

class AssignTO(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.assignments = {}  # Store persistent assignments

    @commands.command(name='assignto')
    async def assign_to(self, ctx):
        prob_officer_role_id = 1306380788056723578
        to_role_id = 1306458665410236436
        loa_role_id = 1325571347673251971
        target_channel_id = 1292569010407346257

        guild = ctx.guild
        target_channel = guild.get_channel(target_channel_id)

        if not target_channel:
            await ctx.send("Error: Target channel not found.")
            return

        prob_officers = [member for member in guild.members if prob_officer_role_id in [role.id for role in member.roles]]
        tos = [member for member in guild.members if to_role_id in [role.id for role in member.roles]]

        if not prob_officers:
            await ctx.send("Error: No Probationary Officers found.")
            return
        if not tos:
            await ctx.send("Error: No TOs found.")
            return

        # Filter out probationary officers already assigned or on LOA
        unassigned_probs = []
        for prob in prob_officers:
            if prob.id in [p.id for to in self.assignments.values() for p in to]:
                continue
            if loa_role_id in [role.id for role in prob.roles]:
                continue
            unassigned_probs.append(prob)

        # Perform new assignments only for unassigned probationary officers
        random.shuffle(unassigned_probs)
        temp_assignments = {to: self.assignments.get(to, []) for to in tos}  # Keep existing assignments

        while unassigned_probs:
            for to in tos:
                if unassigned_probs:
                    temp_assignments[to].append(unassigned_probs.pop())

        # Update persistent assignments
        self.assignments = temp_assignments

        embed = discord.Embed(
            title="TOs & Probationary Officers Assignation",
            description="Here is the list of all Probationary Officers with their assigned TOs.",
            color=discord.Color.blue()
        )

        for to, assigned_probs in self.assignments.items():
            field_value = ""
            for prob in assigned_probs:
                if loa_role_id in [role.id for role in prob.roles]:
                    field_value += f"- {prob.mention} (is on LOA)\n"
                else:
                    field_value += f"- {prob.mention}\n"
            if len(field_value) > 1024:
                field_value = field_value[:1000] + "... (truncated)"
            embed.add_field(
                name=f"{to.display_name} ({to.mention})",
                value=field_value or "No Probationary Officers assigned.",
                inline=False
            )

        if not any(self.assignments.values()):
            embed.add_field(
                name="Assignments",
                value="No assignments could be made.",
                inline=False
            )

        try:
            await target_channel.send(embed=embed)
            await ctx.send(f"Assignments have been posted in {target_channel.mention}.")
        except discord.HTTPException as e:
            await ctx.send(f"Error sending embed: {e}")

async def setup(bot):
    await bot.add_cog(AssignTO(bot))
