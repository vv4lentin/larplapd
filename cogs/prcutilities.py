import discord
from discord.ext import commands
import requests
import json

class PRCUtilities(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        # ER:LC API configuration
        self.api_url = "https://api.policeroleplay.community/v1/server/command"
        self.api_key = "MjPhOXrhyljSrtoLkjwM-ZtLKrsmGAdADRCPKXOOLSDazgluQaWSSXFiVtaKW"  # Hardcoded API key
        self.headers = {
            "server-key": self.api_key,
            "Content-Type": "application/json"
        }

    @commands.command(name="execute")
    async def execute_command(self, ctx, *, command: 
        # Restrict to users with administrator permissions
        if not ctx.author.guild_permissions.administrator:
            await ctx.send("You need administrator permissions to use this command.")
            return

        # Prepare the payload
        payload = {
            "command": command
        }

        try:
            # Send POST request to the API
            response = requests.post(
                self.api_url,
                headers=self.headers,
                data=json.dumps(payload)
            )

            # Handle response
            if response.status_code in (200, 201):
                try:
                    response_data = response.json()
                    message = response_data.get("message", "Command executed successfully.")
                    await ctx.send(f"Command `{command}` sent successfully!\nResponse: {message}")
                except json.JSONDecodeError:
                    await ctx.send(f"Command `{command}` sent successfully!\nResponse: {response.text}")
            else:
                await ctx.send(f"Failed to execute command `{command}`.\nError: {response.status_code} - {response.text}")

        except requests.exceptions.RequestException as e:
            await ctx.send(f"Error contacting the ER:LC API: {str(e)}")

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"{self.__class__.__name__} cog is loaded.")

async def setup(bot):
    await bot.add_cog(PRCUtilities(bot))
