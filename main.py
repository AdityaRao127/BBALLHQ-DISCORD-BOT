from discord.ext import commands
import os
from dotenv import load_dotenv
import discord
from stats import get_player_stats, get_team_stats 
from shotchart import shot_map
from discord.ui import View, Button
from playbyplay import get_play_by_play, fetch_live_games, fetch_ongoing_game_ids
from news import fetch_feed
import schedule 
import time
import feedparser
import re
from datetime import datetime
import asyncio
import tempfile
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import pandas as pd
import aiohttp
from collections import deque
import logging

# Load the environment variable
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
CHANNEL = os.getenv('DISCORD_CHANNEL')

bot = commands.Bot(command_prefix='!', intents=discord.Intents.all(), hearbeat_timeout=60)

POSITION_MAP = {
    "PG": "Point Guard",
    "SG": "Shooting Guard",
    "SF": "Small Forward",
    "PF": "Power Forward",
    "C": "Center",
    "G": "Guard",
    "F": "Forward"
}

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class OptionsDropdown(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label='Live NBA Scores', description='Live scores from nba games 🏀'),
            discord.SelectOption(label='Play-by-play', description='NBA play-by-play of the game 📢'),
            discord.SelectOption(label='Watch Games', description='Watch live 📺'),
            discord.SelectOption(label='Player Stats', description='Player stats📊'),
            discord.SelectOption(label='Team Stats', description='Team_stats📊'),
            discord.SelectOption(label='Injury Report', description='Latest injury report of teams 🚑'),
            discord.SelectOption(label='Shot Chart', description='Shot chart of players 2023-24 season 📈'),
            discord.SelectOption(label='Machine Learning Prediction', description='Simple ML-based predictions of a game🤖'),
            discord.SelectOption(label='Latest NBA News', description='Latest news from trusted NBA reporters 📰'),
        ]
        super().__init__(placeholder='Choose an option', options=options, min_values=1, max_values=1)
        self.old_stories = deque(maxlen=3)
        self.seen_stories = set()  # Track seen stories

    async def callback(self, interaction: discord.Interaction):
        if self.values[0] == "Live NBA Scores":
            await interaction.response.defer()
            live_scores_text = await fetch_live_games()
            time.sleep(1)  
            await interaction.followup.send(live_scores_text)
        
        elif self.values[0] == "Play-by-play":
            await interaction.response.defer()
            ongoing_games = await fetch_ongoing_game_ids()
            time.sleep(1)  # Add a small delay after fetching ongoing games
            if ongoing_games:
                view = LiveGamesView(ongoing_games)
                await interaction.followup.send("Select a game to view play-by-play details:", view=view)
            else:
                await interaction.followup.send("No live games available at the moment.")
        elif self.values[0] == "Watch Games":
            pass
        elif self.values[0] == "Player Stats":
            modal = PlayerStats(timeout=180.0)  
            await interaction.response.send_modal(modal)
        elif self.values[0] == "Team Stats":
            await interaction.response.send_modal(TeamStats())
        elif self.values[0] == "Injury Report":
            view = TeamSelectionView()
            await interaction.response.send_message("Select a team to view their injury report:", view=view)
        elif self.values[0] == "Shot Chart":
            await interaction.response.send_modal(ShotChart())
        elif self.values[0] == "Machine Learning Prediction":
            await interaction.response.send_message("This feature is coming soon! Try Player/Team Stats, Live Scores, Shot-Chart, or Latest News instead.")
        elif self.values[0] == "Latest NBA News":
            await interaction.response.defer()
            await interaction.followup.send("Fetching latest NBA news...")

            try:
                news_posts = await fetch_nba_news()
                time.sleep(1)
                if news_posts:
                    embed = discord.Embed(title="📰 NBA News Updates 📰", color=0x1D428A)

                    for post in news_posts:
                        self.seen_stories.add(post['title'])
                        embed.add_field(
                            name=f"New Story",
                            value=(
                                f"```yaml\n"
                                f"{post['title']}\n"
                                f"```\n"
                                f"[Source]({post['link']})\n"
                                f"Posted: {post['time']}\n"
                                f"\n\u200b"
                            ),
                            inline=False
                        )
                        
                        if post not in self.old_stories:
                            self.old_stories.append(post)
                if self.old_stories:
                    old_stories_value = ""
                    for i, post in enumerate(list(self.old_stories)[:3], 1):
                        old_stories_value += (
                            f"**Old Story {i}**\n"
                            f"{post['title']}\n"
                            f"[Source]({post['link']})\n"
                            f"Posted: {post['time']}\n\n"
                        )
                    embed.add_field(name="Old Stories", value=old_stories_value, inline=False)
                    embed.set_footer(text="Stories taken from r/nba", icon_url="https://www.redditstatic.com/desktop2x/img/favicon/android-icon-192x192.png")
                    await interaction.followup.send(embed=embed)
                else:
                    await interaction.followup.send("No new updates found from specified reporters. Please try again later.")
            except Exception as e:
                logger.error(f"Error fetching NBA news: {str(e)}")
                await interaction.followup.send(f"An error occurred while fetching news: {str(e)}")
                print(f"Error details: {e}")

class PlayerStats(discord.ui.Modal, title="Player Stats"):
    player_name = discord.ui.TextInput(label="Enter the NBA player's name:", style=discord.TextStyle.short)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer()
        loading_player_message = await interaction.followup.send(f"Loading {self.player_name.value.title()} stats...")
        logger.debug(f"Fetching stats for player: {self.player_name.value}")
        player_stats_embed = await get_player_stats(self.player_name.value)
        logger.debug("Player stats fetched successfully")
        await loading_player_message.edit(content=None, embed=player_stats_embed)

class TeamStats(discord.ui.Modal, title="Team Stats"):
    team_name = discord.ui.TextInput(label="Enter an NBA team name:", style=discord.TextStyle.short)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer()
        loading_message = await interaction.followup.send(f"Loading {self.team_name.value.title()} stats...")
        team_stats = await get_team_stats(self.team_name.value)
        await loading_message.edit(content=team_stats)

# new view for shotcharts
class ChartTypeView(discord.ui.View):
    def __init__(self, player_name):
        super().__init__()
        self.player_name = player_name

    @discord.ui.button(label="Regular Shot Chart", style=discord.ButtonStyle.primary)
    async def regular_chart_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        file_path, error = await shot_map(self.player_name, chart_type='regular')
        if file_path:
            await interaction.followup.send(file=discord.File(fp=file_path, filename='shot_chart.png'))
            os.remove(file_path)
        else:
            await interaction.followup.send(f"An error occurred: {error}")

    @discord.ui.button(label="Heatmap Shot Chart", style=discord.ButtonStyle.danger)
    async def heatmap_chart_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        file_path, error = await shot_map(self.player_name, chart_type='heatmap')
        if file_path:
            await interaction.followup.send(file=discord.File(fp=file_path, filename='heatmap_chart.png'))
            os.remove(file_path)
        else:
            await interaction.followup.send(f"An error occurred: {error}")

class ShotChart(discord.ui.Modal, title="Shot Chart"):
    player_chart_name = discord.ui.TextInput(label="Enter the NBA player's name:")

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer()
        view = ChartTypeView(self.player_chart_name.value)
        await interaction.followup.send("Select chart type:", view=view)

class LiveGamesView(discord.ui.View):
    def __init__(self, ongoing_games):
        super().__init__()
        self.last_action_numbers = {}
        for game in ongoing_games:
            button = discord.ui.Button(label=f"{game['matchup']} @ {game['time']}",
                                       style=discord.ButtonStyle.primary,
                                       custom_id=f"game_{game['gameId']}")
            button.callback = self.handle_button_click
            self.add_item(button)
            self.last_action_numbers[game['gameId']] = -1

    async def handle_button_click(self, interaction: discord.Interaction):
        game_id = interaction.data['custom_id'].split('_')[1]
        last_action_number = self.last_action_numbers.get(game_id, -1)
        await interaction.response.defer(ephemeral=True)

        start_time = datetime.now()
        game_ended = False

        while True:
            try:
                plays, last_action_number = await get_play_by_play(game_id, last_action_number)
                time.sleep(1)  # Add a small delay after each play-by-play fetch
                if plays:
                    for play in reversed(plays):  # Iterate over plays in reverse order
                        formatted_play = f"`{play['actionNumber']}` **{play['period']}:{play['clock']}** ({play['actionType']} {play['description']})"
                        await interaction.followup.send(formatted_play)
                    self.last_action_numbers[game_id] = last_action_number
                elif not plays:
                    # 25 minutes check since last play(cause halftime is 15)
                    if (datetime.now() - start_time).total_seconds() / 60 > 25:
                        await interaction.followup.send("No new plays in the last 25 minutes. Ending play-by-play.")
                        break
                else:
                    # Check if the game has ended
                    live_games = await fetch_live_games()
                    for game in live_games:
                        if game['gameId'] == game_id and game['gameStatus'] == 3:
                            if game['homeTeam']['score'] > game['awayTeam']['score']:
                                winner = f"{game['homeTeam']['teamName']} win"
                            else:
                                winner = f"{game['awayTeam']['teamName']} win"
                            await interaction.followup.send(f"Game ended! Final score: {game['awayTeam']['score']} - {game['homeTeam']['score']}, ***{winner}***")
                            game_ended = True
                            break

                    if game_ended:
                        break

                    await asyncio.sleep(0.1)

            except Exception as e:
                logger.error(f"Error during play-by-play interaction: {e}")
                await interaction.followup.send(f"Error: {str(e)}")
                break

class DropdownView(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.add_item(OptionsDropdown())

# Add this new class after the existing dropdown classes
class TeamSelectionDropdown(discord.ui.Select):
    def __init__(self, teams):
        options = [discord.SelectOption(label=team, value=team) for team in teams]
        super().__init__(placeholder="Select a team", options=options)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        team = self.values[0]
        injury_report_embed = await fetch_injury_report(team)
        await interaction.followup.send(embed=injury_report_embed)

class TeamSelectionView(discord.ui.View):
    def __init__(self):
        super().__init__()
        all_teams = [
            "Atlanta", "Boston", "Brooklyn", "Charlotte",
            "Chicago", "Cleveland", "Dallas", "Denver",
            "Detroit", "Golden St.", "Houston", "Indiana",
            "L.A. Clippers", "L.A. Lakers", "Memphis", "Miami",
            "Milwaukee", "Minnesota", "New Orleans", "New York",
            "Oklahoma City", "Orlando", "Philadelphia", "Phoenix",
            "Portland", "Sacramento", "San Antonio", "Toronto",
            "Utah", "Washington"
        ]
        
        # Split teams into groups of 25 or less
        for i in range(0, len(all_teams), 25):
            self.add_item(TeamSelectionDropdown(all_teams[i:i+25]))

async def fetch_injury_report(team):
    logger.debug(f"Fetching injury report for team: {team}")
    url = "https://www.cbssports.com/nba/injuries/"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                soup = BeautifulSoup(await response.text(), 'html.parser')
                time.sleep(1)  # Add a small delay after fetching and parsing the injury report
                team_section = soup.find('div', class_='TeamLogoNameLockup-name', string=team)
                if team_section:
                    injury_table = team_section.find_next('table', class_='TableBase-table')
                    if injury_table:
                        embed = discord.Embed(title=f"🏀 Injury Report for {team}", color=0x1E90FF)
                        embed.set_thumbnail(url="https://i.imgur.com/9gkhv87.png")  # NBA logo
                        rows = injury_table.find_all('tr')[1:]  
                        for row in rows:
                            cols = row.find_all('td')
                            if len(cols) >= 4:
                                player_element = cols[0].find('span', class_='CellPlayerName--long')
                                if player_element:
                                    player = player_element.text.strip()
                                else:
                                    player = cols[0].text.strip()
                                position = cols[1].text.strip()
                                updated = cols[2].text.strip()
                                injury = cols[3].text.strip()
                                comment = cols[4].text.strip() if len(cols) > 4 else "N/A"

                                full_position = POSITION_MAP.get(position, position)
                                
                                embed.add_field(
                                    name=f"**__{player}__**",
                                    value=(
                                        f"```yaml\n"
                                        f"Position: {full_position}\n"
                                        f"```\n"
                                        f"```fix\n"
                                        f"Injury: {injury}\n"
                                        f"```\n"
                                        f"```css\n"
                                        f"Estimated Return: {comment}\n"
                                        f"```"
                                    ),
                                    inline=False
                                )
                                embed.add_field(name="\u200b", value="\u200b", inline=False)  
                        if not embed.fields:
                            embed.description = "✅ No injuries reported for this team."
                        embed.set_footer(text=f"Data from CBS Sports | Last Updated: {updated}", icon_url="https://sports.cbsimg.net/images/cbss/ui5/cbssportsv2_200x200.png")
                        logger.debug("Injury report fetched and processed successfully")
                        return embed
                    else:
                        return discord.Embed(title=f"🏀 Injury Report for {team}", description="No injury information found for this team.", color=0xFF5733)
                else:
                    return discord.Embed(title="❌ Error", description="Team not found in the injury report.", color=0xFF0000)
            else:
                logger.error(f"Failed to fetch injury data. Status code: {response.status}")
                return discord.Embed(title="❌ Error", description="Failed to fetch injury data. Please try again later.", color=0xFF0000)

async def fetch_nba_news():
    url = "https://old.reddit.com/r/nba/new/"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, headers=headers, ssl=False) as response:
                if response.status == 200:
                    soup = BeautifulSoup(await response.text(), 'html.parser')
                    time.sleep(1)  # Add a small delay after fetching and parsing the news
                    posts = soup.find_all('div', class_='thing')
                    
                    news_posts = []
                    for post in posts:
                        title_element = post.find('a', class_='title')
                        time_element = post.find('time', class_='live-timestamp')
                        if title_element and time_element:
                            title = title_element.text.strip()
                            if any(reporter in title for reporter in [
                                "[Charania]", "[Koreen]", "[Lewenberg]", "[Slater]", "[Stein]", "[Haynes]", "[Woj]",
                                "[Amick]", "[Andrews]", "[Bontemps]", "[Buckner]", "[Fischer]", "[Ganguli]", "[Golliver]",
                                "[Goodwill]", "[Holmes]", "[MacMahon]", "[Marks]", "[Noh]", "[Pelton]", "[Reynolds]",
                                "[Rohlin]", "[Scotto]", "[Smith]", "[Spears]", "[Vecenie]", "[Vorkunov]", "[Windhorst]",
                                "[Wojnarowski]", "[Woo]", "[Youngmisuk]", "[Benson]", "[Chouinard]", "[Rowland]", "[Williams]",
                                "[Bulpett]", "[Forsberg]", "[Himmelsbach]", "[King]", "[Murphy]", "[Robb]", "[Washburn]",
                                "[Weiss]", "[Lewis]", "[Phillips-Keaton]", "[Sturm]", "[Triplett]", "[Boone]", "[Gottlieb]",
                                "[Johnson]", "[Mayberry]", "[Poe]", "[Schaefer]", "[Westerlund]", "[Fedor]", "[Russo]",
                                "[Afseth]", "[Caplan]", "[Cato]", "[Townsend]", "[Benedetto]", "[Dempsey]", "[Durando]",
                                "[Rush]", "[Singer]", "[Wind]", "[Beard]", "[Curtis]", "[Edwards]", "[Langlois]", "[Sankofa]",
                                "[Burke]", "[Holmes]", "[Kawakami]", "[Letourneau]", "[Poole]", "[Slater]", "[Thompson]",
                                "[Bijani]", "[Feigen]", "[Gatlin]", "[Iko]", "[Spolane]", "[Williams]", "[Agness]", "[East]",
                                "[Azarly]", "[Esnaashari]", "[Greif]", "[Linn]", "[Murray]", "[Russo]", "[Buha]", "[Goon]",
                                "[McMenamin]", "[Trudell]", "[Turner]", "[Woike]", "[Cole]", "[Giannotto]", "[Herrington]",
                                "[Parrish]", "[Chiang]", "[Jackson]", "[Manso]", "[Winderman]", "[Madden]", "[Nehm]",
                                "[Owczarski]", "[Frederick]", "[Hine]", "[Krawcyznski]", "[Moore]", "[Wolfson]", "[Clark]",
                                "[Eichenhofer]", "[Guillory]", "[Lopez]", "[Begley]", "[Hahn]", "[Katz]", "[Macri]",
                                "[Popper]", "[Winfield]", "[Almanza]", "[Mussatto]", "[Parker]", "[Rahbar]", "[Schlecht]",
                                "[Price]", "[Bodner]", "[Mizell]", "[Neubeck]", "[Pompey]", "[Bourguet]", "[Gambadoro]",
                                "[King]", "[Olson]", "[Rankin]", "[Zimmerman]", "[Highkin]", "[Holdahl]", "[Quick]",
                                "[Christensen]", "[Cunningham]", "[Dave]", "[Ham]", "[Finger]", "[Garcia]", "[McDonald]",
                                "[Orsborn]", "[Tynan]", "[Grange]", "[Lewenberg]", "[Lou]", "[Koreen]", "[Murphy]",
                                "[Smith]", "[Uthayakumar]", "[Wolstat]", "[Anderson]", "[Jones]", "[Larsen]", "[Locke]",
                                "[Todd]", "[Walden]", "[Aldridge]", "[Cole]", "[Dalal]", "[Hughes]", "[Miller]", "[Robbins]",
                                "[Wallace]"
                            ]):
                                link = title_element['href']
                                if not link.startswith('http'):
                                    link = f"https://old.reddit.com{link}"
                                time_ago = time_element.text.strip()
                                news_posts.append({'title': title, 'link': link, 'time': time_ago})
                        
                        if len(news_posts) >= 3:
                            break
                    
                    return news_posts
        except Exception as e:
            logger.error(f"Error fetching NBA news: {str(e)}")
    
    return []

@bot.command()
async def dropdown(ctx):
    """Sends a message with a dropdown."""
    await ctx.send('Please select an option:', view=DropdownView())

@bot.command()
async def nba(ctx):
    """Sends a message with a dropdown."""
    await ctx.send('Please select an option:', view=DropdownView())

@bot.command()
async def hi(ctx):
    """Greet users and provide instructions."""
    await ctx.send('Hello, I am an NBA bot. Type !dropdown to get started!')

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')

bot.run(TOKEN)