import sys
from datetime import datetime, timedelta
import os
import discord
import requests
from discord.ext import commands
from dotenv import load_dotenv
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from PIL import Image
import io

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
    class MyBot(commands.Bot):
        start_time = datetime.utcnow()
        games_dict = {
            "Counter-Strike": ["csgo", "cs:go", "counter strike", "counter-strike", "counter strike: global offensive",
                               "cs", "cs go", "cs: go", "cs2", "cs 2"],
            "Rainbow Six Siege": ["rainbow six", "rainbow six siege", "r6", "r6s", "rainbow 6", "rainbow 6 siege"],
            "League of Legends": ["league of legends", "lol", "league"],
            "Rocket League": ["rocket league", "rl", "rocket soccer", "rl: rocket league", "car soccer"],
            "Overwatch 2": ["overwatch", "ow", "overwatch 2", "overwatch2", "overwatch ii", "overwatch 2"],
            "Valorant": ["valorant", "val", "valor", "valor ant", "valor-ant", "v", "va", "valo", "valo-rant"],
            "Splatoon": ["splatoon", "splat", "splat3", "spoon", "sploon", "spl"]
        }

        async def setup_hook(self):
            print("Bot starting")
            result = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range="Players").execute()
            values = result.get('values', [])
            if not values:
                sys.exit("No data found.")
            # self.games_dict = self.convert_to_dict(values)

        @staticmethod
        def convert_to_dict(data):
            result_dict = {}
            for row in data:
                key = row[0]
                values = row[1:]
                result_dict[key] = values
            return result_dict

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
        games = bot.games_dict

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
                    result = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range="Players").execute()
                    values = result.get('values', [])
                    rows = []

                    if not values:
                        print('No data found.')
                    else:
                        game_row = None
                        synonyms = [game_title.lower()] + games[
                            game_title]  # including the title in the synonyms list for matching

                        for idx, row in enumerate(values):
                            if row and row[3].lower() in synonyms:
                                game_row = idx
                                rows.append(row)

                        if game_row is not None:
                            embed.description = f"Here is the roster for the {game_title} team"
                            #team names empty array
                            team_names = []
                            #player names empty 2d array
                            player_names = []

                            for row in rows:
                                # Old code:
                                # embed.add_field(name=row[1], value="\n".join(row[2:]), inline=True)
                                # Now the first column is gamertag, and 5th column is the team name
                                # Show each player's gamertag and group based on the team name
                                gamertag = row[0]
                                team_name = row[4]
                                if team_name not in team_names:
                                    team_names.append(team_name)
                                    player_names.append([gamertag])
                                else:
                                    idx = team_names.index(team_name)
                                    player_names[idx].append(gamertag)
                            for i in range(len(team_names)):
                                embed.add_field(name=team_names[i], value="\n".join(player_names[i]), inline=True)
                        else:
                            embed.description = "Sorry, we don't have data for that game yet, " \
                                                "please wait for an organizer to update the data."
                except HttpError as error:
                    print(f"An error occurred: {error}")

            else:
                embed.description = "Sorry, we don't have a team for that game."

        await ctx.reply(embed=embed)

    """
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
                                               "`/help` - Shows help for the bot\n"
                                               "`/uptime` - Shows the bot uptime", inline=False)
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
    """

    @bot.hybrid_command(name="uptime", description="Shows the bot's uptime")
    async def uptime(ctx: commands.Context):
        embed = discord.Embed(title="UF Esports Bot Uptime", color=0x00ff00)
        now = datetime.utcnow()
        delta = now - bot.start_time
        months = delta.days // 30
        days = delta.days % 30
        hours = delta.seconds // 3600
        minutes = (delta.seconds % 3600) // 60
        seconds = delta.seconds % 60
        embed.description = f"{months} months, {days} days, {hours} hours, {minutes} minutes, {seconds} seconds"

        await ctx.reply(embed=embed)

    """
    @bot.command(name="overlay")
    async def overlay(ctx, background_url: str, img1_url: str, img2_url: str):
        try:
            image = overlay_images(background_url, img1_url, img2_url)
            await ctx.send(file=discord.File(fp=image, filename='overlay.png'))
        except Exception as e:
            await ctx.send(f"An error occurred: {str(e)}")
    """
    # Starts the bot (for real)
    bot.run(TOKEN)


def overlay_images(background_url, img1_url, img2_url):
    # Convert the URL into a bytes-like object using requests
    bg = Image.open(io.BytesIO(requests.get(background_url).content))
    img1 = Image.open(io.BytesIO(requests.get(img1_url).content))
    img2 = Image.open(io.BytesIO(requests.get(img2_url).content))

    # Calculate new dimensions for img1 and img2
    new_width = int(bg.width / 2)
    new_height = bg.height

    # Resize img1 and img2
    img1 = img1.resize((new_width, new_height), Image.LANCZOS)
    img2 = img2.resize((new_width, new_height), Image.LANCZOS)

    bg.paste(img1, (0, 0))
    bg.paste(img2, (0, 0))

    # Convert back to bytes for Discord
    arr = io.BytesIO()
    bg.save(arr, format='PNG')
    arr.seek(0)
    return arr
