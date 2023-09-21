import discord
from discord.ext import commands, tasks
from datetime import date, datetime
import datetime as dt
import os
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('TOKEN')


# Function to start the bot
def run_bot():
    # Set up timed loop functions
    class MyBot(commands.Bot):
        async def setup_hook(self):
            print("Bot starting")

    # Creates instance of the bot that uses the prefix "^" for commands
    bot = MyBot(command_prefix="^", intents=discord.Intents.all())

    @bot.event
    async def on_ready():
        print("Bot is now running")
        try:
            synced = await bot.tree.sync()
            print(f"Synced {len(synced)} command(s)")
        except Exception as e:
            print(e)

    @bot.hybrid_command(name="roster", description="Shows roster for the current team")
    async def roster(ctx: commands.Context, team: str = None):
        embed = discord.Embed(title="UF Esports Roster", color=0x00ff00)
        if team is None:
            # If no team is provided, reply with a list of available teams (modify accordingly)
            embed.description = "We currently have teams for the following games:\n- Game 1\n- Game 2\n- Game 3"
        else:
            # Logic to fetch and embed the roster for the specified team can be added here
            pass  # Remove this line when you add the logic for specific teams
        await ctx.reply(embed=embed)

    # Starts the bot (for real)
    bot.run(TOKEN)

