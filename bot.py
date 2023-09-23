import discord
from discord.ext import commands, tasks
from datetime import date, datetime
import datetime as dt
import os
from dotenv import load_dotenv
from google.auth.transport.requests import Request
from google.oauth2.service_account import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


# Setup the Google Sheets API client
SCOPE = ['https://www.googleapis.com/auth/spreadsheets']
SPREADSHEET_ID = os.getenv('SPREADSHEET_ID')


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
    credentials = Credentials.from_service_account_file("gatoresports.json", scopes=SCOPE)
    service = build('sheets', 'v4', credentials=credentials)
    sheet = service.spreadsheets()

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

        # Mapping of the game synonyms to the full name
        games = {
            "counter strike": ["csgo", "cs:go", "counter strike", "counter-strike",
                               "counter strike: global offensive", "cs"],
            "rainbow six": ["rainbow six", "rainbow six siege", "r6", "r6s", "rainbow 6", "rainbow 6 siege"],
            "league of legends": ["league of legends", "lol", "league"],
            "rocket league": ["rocket league", "rl"],
            "overwatch": ["overwatch", "ow"]
        }

        if team is None:
            # If no team is provided, reply with a list of available teams
            embed.description = "We currently have teams for the following games: " + ", ".join(games.keys())
        else:
            team = team.lower()

            found = False
            for game, synonyms in games.items():
                if team in synonyms:
                    embed.description = f"Here is the roster for the {game.title()} team"
                    found = True
                    if found:
                        print("Found team")
                        try:
                            # Use the sheet object to access the values of the entire sheet
                            # Assuming you're fetching data from the first sheet and its entire range
                            result = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range="Sheet1").execute()
                            values = result.get('values', [])

                            # Check if data is present
                            if not values:
                                print('No data found.')
                            else:
                                # Print each row of the sheet to the console
                                for row in values:
                                    print(', '.join(row))
                        except HttpError as error:
                            print(f"An error occurred: {error}")

                    break
            if not found:
                embed.description = "Sorry, we don't have a team for that game yet"
            pass

        await ctx.reply(embed=embed)

    # Starts the bot (for real)
    bot.run(TOKEN)

