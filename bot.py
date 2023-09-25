from datetime import datetime, timedelta
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

    @bot.hybrid_command(name="team", description="Shows roster for the current team")
    async def t(ctx: commands.Context, team: str = None):
        await roster(ctx, team)

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
    async def socials(ctx: commands.Context):
        try:
            # Fetch data from Google Sheets
            result = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range="Socials").execute()
            values = result.get('values', [])
            embed = discord.Embed(title="UF Esports Socials", color=0x00ff00)

            if not values:
                return await ctx.reply("Failed to fetch social links. Please try again later.")
            else:
                for row in values:
                    if not row:
                        break
                    name = row[0]
                    link = row[1]
                    embed.add_field(name=name, value=link, inline=False)

        except HttpError as error:
            print(f"An error occurred: {error}")
            return await ctx.reply("Failed to fetch social links. Please try again later.")

        await ctx.reply(embed=embed)

    bot.remove_command("help")

    @bot.hybrid_command(name="help", description="Shows help for the bot")
    async def help(ctx: commands.Context):
        embed = discord.Embed(title="UF Esports Bot Help", color=0x00ff00)
        embed.add_field(name="Commands", value="`/roster <game>` - Shows roster for the current team\n"
                                               "`/socials` - Shows socials for the current team\n"
                                               "`/gbm` - Shows the upcoming GBM\n"
                                               "`/help` - Shows help for the bot", inline=False)
        await ctx.reply(embed=embed)

    @bot.hybrid_command(name="gbm", description="Shows the upcoming GBM")
    async def gbm(ctx: commands.Context):
        try:
            # Fetch data from Google Sheets
            result = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range="GBM").execute()
            values = result.get('values', [])
            embed = discord.Embed(title="UF Esports GBM", color=0x00ff00)

            if not values:
                return await ctx.reply("Failed to fetch GBM info. Please try again later.")
            else:
                upcoming_gbm = None
                latest_gbm = None
                data_rows = values[1:]  # Skip the header row
                data_rows.sort(key=lambda row: datetime.strptime(row[0], '%B %d, %Y, %I:%M %p'))
                for r in data_rows:
                    date_str, location, description = r
                    date = datetime.strptime(date_str, '%B %d, %Y, %I:%M %p')
                    if date < datetime.now():
                        latest_gbm = r
                    if date > datetime.now() and upcoming_gbm is None:
                        upcoming_gbm = r
                        break

                if upcoming_gbm:
                    date_str, location, description = upcoming_gbm
                    embed.add_field(name="Date", value=date_str, inline=False)
                    embed.add_field(name="Location", value=location, inline=False)
                    embed.add_field(name="Description", value=description, inline=False)
                elif latest_gbm:
                    date_str, location, description = latest_gbm
                    embed.description = "There are no upcoming GBMs scheduled, the latest one was on " + date_str + "."
                else:
                    embed.description = "There are no upcoming GBMs scheduled."

                return await ctx.reply(embed=embed)

        except HttpError as error:
            print(f"An error occurred: {error}")
            return await ctx.reply("Failed to fetch social links. Please try again later.")

    # Starts the bot (for real)
    bot.run(TOKEN)
