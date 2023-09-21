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

    #
    @bot.hybrid_command(name="roster", description="Shows roster for the current team")
    async def roster(ctx: commands.Context):
        embed = discord.Embed(title="Current Roster:", color=0xff8585)
        await ctx.reply(embed=embed)

    # Starts the bot (for real)
    bot.run(TOKEN)
