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
    bot = MyBot(command_prefix="/", intents=discord.Intents.all())

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
            embed.description = "We currently have teams for the following games: " \
                                "Counter Strike, Rainbow Six, League of Legends, Rocket League, and Overwatch"
        else:
            team = team.lower()  # Convert the team name to lowercase

            counter_strike = ["csgo", "cs:go", "counter strike", "counter-strike", "counter strike: global offensive"]
            rainbow_six = ["rainbow six", "rainbow six siege", "r6", "r6s", "rainbow 6", "rainbow 6 siege"]
            league_of_legends = ["league of legends", "lol", "league"]
            rocket_league = ["rocket league", "rl"]
            overwatch = ["overwatch", "ow"]

            if team in counter_strike:
                embed.description = "Here is the roster for the Counter Strike team"
            elif team in rainbow_six:
                embed.description = "Here is the roster for the Rainbow Six team"
            elif team in league_of_legends:
                embed.description = "Here is the roster for the League of Legends team"
            elif team in rocket_league:
                embed.description = "Here is the roster for the Rocket League team"
            elif team in overwatch:
                embed.description = "Here is the roster for the Overwatch team"
            else:
                embed.description = "Sorry, we don't have a team for that game yet"

            # Logic to fetch and embed the roster for the specified team can be added here
            pass  # Remove this line when you add the logic for specific teams
        await ctx.reply(embed=embed)

    # Starts the bot (for real)
    bot.run(TOKEN)

