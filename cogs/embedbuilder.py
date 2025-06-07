import discord
from discord.ext import commands
import re
import uuid

class EmbedBuilder(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.default_color = discord.Color.blue()  # Default embed color
        self.default_thumbnail = None  # Optional: Set a default thumbnail URL
        self.view_timeout = 600  # View timeout in seconds (10 minutes)

    class EmbedModal(discord.ui.Modal, title="Create Custom Embed"):
        def __init__(self, default_color, default_thumbnail):
            super().__init__(timeout=300)  # Modal timeout: 5 minutes
            self.default_color = default_color
            self.default_thumbnail = default_thumbnail

            self.name = discord.ui.TextInput(
                label="Name",
                placeholder="Enter the title for the embed",
                max_length=256,
                required=True
            )
            self.description = discord.ui.TextInput(
                label="Description",
                placeholder="Enter the description",
                style=discord.TextStyle.paragraph,
                max_length=4000,
                required=True
            )
            self.footer = discord.ui.TextInput(
                label="Footer",
                placeholder="Enter footer text (optional)",
                max_length=2048,
                required=False
            )
            self.thumbnail = discord.ui.TextInput(
                label="Thumbnail URL",
                placeholder="Enter image URL for thumbnail (optional)",
                max_length=2048,
                required=False
            )
            self.color = discord.ui.TextInput(
                label="Color (Hex)",
                placeholder="Enter hex color (e.g., #FF0000) or leave blank",
                max_length=7,
                required=False
            )

            self.add_item(self.name)
            self.add_item(self.description)
            self.add_item(self.footer)
            self.add_item(self.thumbnail)
            self.add_item(self.color)

        async def on_submit(self, interaction: discord.Interaction):
            # Validate color
            color = self.default_color
            if self.color.value:
                try:
                    hex_color = self.color.value.lstrip('#')
                    if re.match(r'^[0-9A-Fa-f]{6}$', hex_color):
                        color = discord.Color(int(hex_color, 16))
                    else:
                        await interaction.response.send_message(
                            "Invalid hex color format! Using default color.",
                            ephemeral=True
                        )
                except ValueError:
                    await interaction.response.send_message(
                        "Invalid hex color! Using default color.",
                        ephemeral=True
                    )

            # Create embed
            embed = discord.Embed(
                title=self.name.value,
                description=self.description.value,
                color=color
            )

            # Set footer if provided
            if self.footer.value:
                embed.set_footer(text=self.footer.value)

            # Set thumbnail if provided and valid
            thumbnail_url = self.thumbnail.value or self.default_thumbnail
            if thumbnail_url:
                if re.match(r'^https?://[^\s<>"\'\[\]]+\.(?:png|jpg|jpeg|gif|webp)$', thumbnail_url, re.IGNORECASE):
                    embed.set_thumbnail(url=thumbnail_url)
                else:
                    await interaction.response.send_message(
                        "Invalid thumbnail URL! Embed created without thumbnail.",
                        ephemeral=True
                    )

            # Check embed size limits
            total_length = len(self.name.value) + len(self.description.value) + (len(self.footer.value) if self.footer.value else 0)
            if total_length > 6000:
                await interaction.response.send_message(
                    "Embed content exceeds Discord's 6000-character limit!",
                    ephemeral=True
                )
                return

            # Send embed and confirmation
            await interaction.channel.send(embed=embed)
            await interaction.response.send_message(
                "Embed created successfully!",
                ephemeral=True
            )

        async def on_error(self, interaction: discord.Interaction, error: Exception):
            await interaction.response.send_message(
                "An error occurred while creating the embed. Please try again.",
                ephemeral=True
            )

    class EmbedButton(discord.ui.View):
        def __init__(self, default_color, default_thumbnail, view_timeout):
            super().__init__(timeout=view_timeout)  # Pass view_timeout to View
            self.default_color = default_color
            self.default_thumbnail = default_thumbnail

        @discord.ui.button(label="Create Embed", style=discord.ButtonStyle.primary, custom_id=f"embed_button_{uuid.uuid4()}")
        async def create_embed_button(self, interaction: discord.Interaction, button: discord.ui.Button):
            await interaction.response.send_modal(
                EmbedBuilder.EmbedModal(self.default_color, self.default_thumbnail)
            )

    @commands.command(name="embed")
    @commands.has_permissions(send_messages=True, embed_links=True)
    @commands.bot_has_permissions(send_messages=True, embed_links=True)
    @commands.cooldown(1, 30, commands.BucketType.user)
    async def embed_command(self, ctx: commands.Context):
        """Sends a button to create a custom embed via a modal."""
        view = self.EmbedButton(self.default_color, self.default_thumbnail, self.view_timeout)
        await ctx.send("Click the button to create a custom embed!", view=view)

    @embed_command.error
    async def embed_command_error(self, ctx: commands.Context, error: commands.CommandError):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("You need `send_messages` and `embed_links` permissions to use this command.")
        elif isinstance(error, commands.BotMissingPermissions):
            await ctx.send("I need `send_messages` and `embed_links` permissions to execute this command.")
        elif isinstance(error, commands.CommandOnCooldown):
            await ctx.send(f"This command is on cooldown. Try again in {error.retry_after:.1f} seconds.")
        else:
            await ctx.send("An error occurred while executing the command.")

async def setup(bot):
    await bot.add_cog(EmbedBuilder(bot))
