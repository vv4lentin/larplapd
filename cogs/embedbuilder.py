import discord
from discord.ext import commands
import re
import uuid

class EmbedBuilder(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.default_color = discord.Color.blue()  
        self.default_thumbnail = None 
        self.embed_store = {}  

    class EmbedModal(discord.ui.Modal, title="Create Custom Embed"):
        def __init__(self, default_color, default_thumbnail, embed_id=None, existing_embed=None):
            super().__init__()  
            self.default_color = default_color
            self.default_thumbnail = default_thumbnail
            self.embed_id = embed_id

            default_title = existing_embed.title if existing_embed else ""
            default_description = existing_embed.description if existing_embed else ""
            default_footer = existing_embed.footer.text if existing_embed and existing_embed.footer else ""
            default_thumbnail = existing_embed.thumbnail.url if existing_embed and existing_embed.thumbnail else ""
            default_color = f"#{existing_embed.color.value:06x}" if existing_embed else ""

            self.name = discord.ui.TextInput(
                label="Name",
                placeholder="Enter the title for the embed",
                max_length=256,
                required=True,
                default=default_title
            )
            self.description = discord.ui.TextInput(
                label="Description",
                placeholder="Enter the description",
                style=discord.TextStyle.paragraph,
                max_length=4000,
                required=True,
                default=default_description
            )
            self.footer = discord.ui.TextInput(
                label="Footer",
                placeholder="Enter footer text (optional)",
                max_length=2048,
                required=False,
                default=default_footer
            )
            self.thumbnail = discord.ui.TextInput(
                label="Thumbnail URL",
                placeholder="Enter image URL for thumbnail (optional)",
                max_length=2048,
                required=False,
                default=default_thumbnail
            )
            self.color = discord.ui.TextInput(
                label="Color (Hex)",
                placeholder="Enter hex color (e.g., #FF0000) or leave blank",
                max_length=7,
                required=False,
                default=default_color
            )

            self.add_item(self.name)
            self.add_item(self.description)
            self.add_item(self.footer)
            self.add_item(self.thumbnail)
            self.add_item(self.color)

        async def on_submit(self, interaction: discord.Interaction):
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

            embed = discord.Embed(
                title=self.name.value,
                description=self.description.value,
                color=color
            )

            if self.footer.value:
                embed.set_footer(text=self.footer.value)

            thumbnail_url = self.thumbnail.value or self.default_thumbnail
            if thumbnail_url:
                if re.match(r'^https?://[^\s<>"\'\[\]]+\.(?:png|jpg|jpeg|gif|webp)$', thumbnail_url, re.IGNORECASE):
                    embed.set_thumbnail(url=thumbnail_url)
                else:
                    await interaction.response.send_message(
                        "Invalid thumbnail URL! Embed created without thumbnail.",
                        ephemeral=True
                    )

            total_length = len(self.name.value) + len(self.description.value) + (len(self.footer.value) if self.footer.value else 0)
            if total_length > 6000:
                await interaction.response.send_message(
                    "Embed content exceeds Discord's 6000-character limit!",
                    ephemeral=True
                )
                return

            if self.embed_id:
                self.cog.embed_store[self.embed_id] = embed

            await interaction.channel.send(embed=embed)
            await interaction.response.send_message(
                f"Embed {'modified' if self.embed_id else 'created'} successfully! Embed ID: {self.embed_id or str(uuid.uuid4())}",
                ephemeral=True
            )

        async def on_error(self, interaction: discord.Interaction, error: Exception):
            await interaction.response.send_message(
                "An error occurred while processing the embed. Please try again.",
                ephemeral=True
            )

    class EmbedButton(discord.ui.View):
        def __init__(self, default_color, default_thumbnail, cog):
            super().__init__() 
            self.default_color = default_color
            self.default_thumbnail = default_thumbnail
            self.cog = cog

        @discord.ui.button(label="Create Embed", style=discord.ButtonStyle.primary, custom_id=f"embed_button_{uuid.uuid4()}")
        async def create_embed_button(self, interaction: discord.Interaction, button: discord.ui.Button):
            modal = self.cog.EmbedModal(self.default_color, self.default_thumbnail)
            modal.cog = self.cog 
            await interaction.response.send_modal(modal)

    class ModifyButton(discord.ui.View):
        def __init__(self, default_color, default_thumbnail, embed_id, embed, cog):
            super().__init__()
            self.default_color = default_color
            self.default_thumbnail = default_thumbnail
            self.embed_id = embed_id
            self.embed = embed
            self.cog = cog

        @discord.ui.button(label="Modify Embed", style=discord.ButtonStyle.secondary, custom_id=f"modify_button_{uuid.uuid4()}")
        async def modify_embed_button(self, interaction: discord.Interaction, button: discord.ui.Button):
            modal = self.cog.EmbedModal(self.default_color, self.default_thumbnail, self.embed_id, self.embed)
            modal.cog = self.cog  
            await interaction.response.send_modal(modal)

    @commands.command(name="embed")
    @commands.has_permissions(send_messages=True, embed_links=True)
    @commands.bot_has_permissions(send_messages=True, embed_links=True)
    async def embed_command(self, ctx: commands.Context):
        view = self.EmbedButton(self.default_color, self.default_thumbnail, self)
        await ctx.send("Click the button to create a custom embed!", view=view)

    @commands.command(name="copyembed")
    @commands.has_permissions(send_messages=True, embed_links=True)
    @commands.bot_has_permissions(send_messages=True, embed_links=True)
    async def copy_embed(self, ctx: commands.Context, message_id: int):
        try:
            message = await ctx.channel.fetch_message(message_id)
            if not message.embeds:
                await ctx.send("No embeds found in the specified message!", ephemeral=True)
                return

            embed = message.embeds[0]
            embed_id = str(uuid.uuid4())
            self.embed_store[embed_id] = embed
            await ctx.send(f"Embed copied successfully! Use `!pasteembed {embed_id}` to paste it.", ephemeral=True)
        except discord.NotFound:
            await ctx.send("Message not found! Please check the message ID.", ephemeral=True)
        except discord.Forbidden:
            await ctx.send("I don't have permission to access that message!", ephemeral=True)

    @commands.command(name="pasteembed")
    @commands.has_permissions(send_messages=True, embed_links=True)
    @commands.bot_has_permissions(send_messages=True, embed_links=True)
    async def paste_embed(self, ctx: commands.Context, embed_id: str):
        embed = self.embed_store.get(embed_id)
        if not embed:
            await ctx.send("Invalid or expired embed ID!", ephemeral=True)
            return

        await ctx.send(embed=embed)
        await ctx.send(f"Embed pasted successfully! ID: {embed_id}", ephemeral=True)

    @commands.command(name="modifyembed")
    @commands.has_permissions(send_messages=True, embed_links=True)
    @commands.bot_has_permissions(send_messages=True, embed_links=True)
    async def modify_embed(self, ctx: commands.Context, embed_id: str):
        embed = self.embed_store.get(embed_id)
        if not embed:
            await ctx.send("Invalid or expired embed ID!", ephemeral=True)
            return

        view = self.ModifyButton(self.default_color, self.default_thumbnail, embed_id, embed, self)
        await ctx.send("Click the button to modify the embed!", view=view, ephemeral=True)

    @embed_command.error
    @copy_embed.error
    @paste_embed.error
    @modify_embed.error
    async def command_error(self, ctx: commands.Context, error: commands.CommandError):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("You need `send_messages` and `embed_links` permissions to use this command.", ephemeral=True)
        elif isinstance(error, commands.BotMissingPermissions):
            await ctx.send("I need `send_messages` and `embed_links` permissions to execute this command.", ephemeral=True)
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"Missing required argument: {error.param.name}", ephemeral=True)
        else:
            await ctx.send("An error occurred while executing the command.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(EmbedBuilder(bot))

