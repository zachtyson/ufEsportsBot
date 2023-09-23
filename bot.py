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
            "Counter-Strike": ["csgo", "cs:go", "counter strike", "counter-strike",
                               "counter strike: global offensive", "cs", "cs go", "cs: go", "cs2", "cs 2"],
            "Rainbow Six Siege": ["rainbow six", "rainbow six siege", "r6", "r6s", "rainbow 6", "rainbow 6 siege"],
            "League of Legends": ["league of legends", "lol", "league"],
            "Rocket League": ["rocket league", "rl"],
            "Overwatch": ["overwatch", "ow"],
            "Valorant": ["valorant", "val", "valor", "valor ant", "valor-ant", "v", "va", "valo", "valo-rant"],
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
                        try:
                            # Fetch data from Google Sheets
                            result = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range="Sheet1").execute()
                            values = result.get('values', [])
                            rows = []

                            if not values:
                                print('No data found.')
                            else:
                                game_row = None
                                for idx, row in enumerate(values):
                                    if game.lower() in [s.lower() for s in row[:1]]:

                                        game_row = idx
                                        rows.append(row)

                                if game_row is not None:
                                    for row in rows:
                                        embed.add_field(name=row[1], value="\n".join(row[2:]), inline=True)
                        except HttpError as error:
                            print(f"An error occurred: {error}")

                    break
            if not found:
                embed.description = "Sorry, we don't have a team for that game yet"

        await ctx.reply(embed=embed)

    # Starts the bot (for real)
    bot.run(TOKEN)

