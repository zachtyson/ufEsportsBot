import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Setup the Google Sheets API client
SCOPE = ['https://www.googleapis.com/auth/spreadsheets']
SPREADSHEET_ID = os.getenv('SPREADSHEET_ID')


load_dotenv()
TOKEN = os.getenv('TOKEN')

SERVICE_ACCOUNT_INFO = {
    "type": os.getenv('CREDENTIALS_TYPE'),
    "project_id": os.getenv('CREDENTIALS_PROJECT_ID'),
    "private_key_id": os.getenv('CREDENTIALS_PRIVATE_KEY_ID'),
    "private_key": os.getenv('CREDENTIALS_PRIVATE_KEY').replace('\\n', '\n'),
    "client_email": os.getenv('CREDENTIALS_CLIENT_EMAIL'),
    "client_id": os.getenv('CREDENTIALS_CLIENT_ID'),
    "auth_uri": os.getenv('CREDENTIALS_AUTH_URI'),
    "token_uri": os.getenv('CREDENTIALS_TOKEN_URI'),
    "auth_provider_x509_cert_url": os.getenv('CREDENTIALS_AUTH_PROVIDER_X509_CERT_URL'),
    "client_x509_cert_url": os.getenv('CREDENTIALS_CLIENT_X509_CERT_URL'),
    "universe_domain": os.getenv('CREDENTIALS_UNIVERSE_DOMAIN')
}


# Function to start the bot
def run_bot():
    # Set up timed loop functions
    class MyBot(commands.Bot):
        async def setup_hook(self):
            print("Bot starting")

    # Creates instance of the bot that uses the prefix "^" for commands
    bot = MyBot(command_prefix="/", intents=discord.Intents.all())
    credentials = Credentials.from_service_account_info(SERVICE_ACCOUNT_INFO, scopes=SCOPE)
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
            "Rocket League": ["rocket league", "rl", "rocket soccer", "rl: rocket league", "car soccer"],
            "Overwatch 2": ["overwatch", "ow", "overwatch 2", "overwatch2", "overwatch ii", "overwatch 2"],
            "Valorant": ["valorant", "val", "valor", "valor ant", "valor-ant", "v", "va", "valo", "valo-rant"],
        }

        if team is None:
            # If no team is provided, reply with a list of available teams
            embed.description = "We currently have teams for the following games: " + ", ".join(games.keys())
        else:
            team = team.lower()

            game_title = None
            for title, synonyms in games.items():
                if team in synonyms:
                    game_title = title
                    break

            if game_title:
                try:
                    # Fetch data from Google Sheets
                    result = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range="Rosters").execute()
                    values = result.get('values', [])
                    rows = []

                    if not values:
                        print('No data found.')
                    else:
                        game_row = None
                        synonyms = [game_title.lower()] + games[
                            game_title]  # including the title in the synonyms list for matching

                        for idx, row in enumerate(values):
                            if row and row[0].lower() in synonyms:
                                game_row = idx
                                rows.append(row)

                        if game_row is not None:
                            embed.description = f"Here is the roster for the {game_title} team"
                            for row in rows:
                                embed.add_field(name=row[1], value="\n".join(row[2:]), inline=True)
                        else:
                            embed.description = "Sorry, we don't have data for that game yet, " \
                                                "please wait for an organizer to update the data."
                except HttpError as error:
                    print(f"An error occurred: {error}")

            else:
                embed.description = "Sorry, we don't have a team for that game."

        await ctx.reply(embed=embed)

    @bot.hybrid_command(name="socials", description="Shows socials for the current team")
    async def socials(ctx: commands.Context, team: str = None):
        embed = discord.Embed(title="UF Esports Socials", color=0x00ff00)
        embed.add_field(name="Twitter/X", value="https://twitter.com/UFEsportsClub", inline=False)
        embed.add_field(name="Instagram", value="https://instagram.com/ufclubesports", inline=False)
        embed.add_field(name="Twitch", value="https://twitch.tv/gator_esports", inline=False)
        embed.add_field(name="Discord", value="https://discord.gg/Q2AeDhCPHB", inline=False)


        await ctx.reply(embed=embed)
    # Starts the bot (for real)
    bot.run(TOKEN)

