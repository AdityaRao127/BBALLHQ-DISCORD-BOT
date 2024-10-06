from discord.ext import commands
import os
from dotenv import load_dotenv
import discord
from stats import get_player_stats, get_team_stats 
from shotchart import shot_map
from discord.ui import View, Button
from playbyplay import get_play_by_play, fetch_live_games, fetch_ongoing_game_ids
from news import fetch_feed
from discord.ext import commands 
import schedule 
import time
import feedparser
import re
import os
from keep_alive import keep_alive
from datetime import datetime
import asyncio
import tempfile
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import pandas as pd
import aiohttp


# Load the environment variable
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
CHANNEL = os.getenv('DISCORD_CHANNEL')

# Initialize the bot
bot = commands.Bot(command_prefix='!', intents=discord.Intents.all(), hearbeat_timeout=60)

keep_alive()

# Add this position map near the top of your file, after the imports
POSITION_MAP = {
    "PG": "Point Guard",
    "SG": "Shooting Guard",
    "SF": "Small Forward",
    "PF": "Power Forward",
    "C": "Center",
    "G": "Guard",
    "F": "Forward"
}

class OptionsDropdown(discord.ui.Select):
    def __init__(self):
        options=[
            discord.SelectOption(label='Live NBA Scores', description='Live scores from nba games 🏀'),
            discord.SelectOption(label = 'Play-by-play', description='NBA play-by-play of the game 📢'),
            discord.SelectOption(label='Watch Games', description='Watch live 📺'),
            discord.SelectOption(label='Player Stats', description='Player stats📊'),
            discord.SelectOption(label ='Team Stats', description='Team_stats📊'),
            discord.SelectOption(label='Injury Report', description='Latest injury report of teams 🚑'),
            discord.SelectOption(label ='Shot Chart', description='Shot chart of players 2023-24 season 📈'),
            discord.SelectOption(label='Machine Learning Prediction', description='Simple ML-based predictions of a game🤖'),
            discord.SelectOption(label='Latest News', description='Reliable news sources 📰'),
        
        ]
        super().__init__(placeholder='Choose an option', options=options, min_values=1, max_values=1)

    async def callback(self, interaction: discord.Interaction):
        if self.values[0] == "Live NBA Scores":
            live_scores_text = await fetch_live_games()
            await interaction.response.send_message(live_scores_text)
        
        elif self.values[0] == "Play-by-play":
            ongoing_games = await fetch_ongoing_game_ids()
            if ongoing_games:
                view = LiveGamesView(ongoing_games)
                await interaction.response.send_message("Select a game to view play-by-play details:", view=view)
            else:
                await interaction.response.send_message("No live games available at the moment.")
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
        elif self.values[0] == "Latest News":
            await interaction.response.defer()
            await interaction.followup.send("Fetching latest news...")

            try:
                shams_tweets = await fetch_popular_tweets('ShamsCharania', total_scrolls=5)
                if shams_tweets:
                    shams_message = "Shams' Latest Updates:\n"
                    for tweet in shams_tweets[:3]:  #latest 3 tweets
                        shams_message += f"**Tweet Content**:\n{tweet['content']}\n\nAuthor: {tweet['author']}\nRelevancy: {tweet['published']}\n\n"
                    await interaction.followup.send(shams_message)
                else:
                    await interaction.followup.send("No new updates found.")
            except Exception as e:
                await interaction.followup.send(f"An error occurred while fetching tweets: {str(e)}")

async def fetch_popular_tweets(username, total_scrolls=10):
    link = f"https://x.com/{username}"
    data = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(link, timeout=500000)

        initial_height = 0
        final_height = 1000
        for _ in range(total_scrolls):
            await page.mouse.wheel(initial_height, final_height)
            initial_height = final_height
            final_height = final_height + 300
            await asyncio.sleep(4)
            content = await page.content()
            soup = BeautifulSoup(content, 'html.parser')
            all_posts = soup.find_all('div', {'data-testid': 'cellInnerDiv'})

            for post in all_posts:
                check_retweet = post.find('div', {'role': 'link'})

                if check_retweet is None:
                    tweet_element = post.find('div', {'data-testid': 'tweetText'})
                    if tweet_element:
                        tweet = tweet_element.get_text(strip=True)

                        data.append({
                            'content': tweet,
                            'author': username,
                            'published': 'Popular Tweets'
                        })

        await browser.close()

    df = pd.DataFrame(data)
    df.drop_duplicates(inplace=True)
    latest_tweets = df.to_dict('records')
    return latest_tweets

        
class PlayerStats(discord.ui.Modal, title="Player Stats"):
    player_name = discord.ui.TextInput(label="Enter the NBA player's name:", style=discord.TextStyle.short)

    async def on_submit(self, interaction: discord.Interaction):
        # Acknowledge the interaction
        await interaction.response.defer()
        loading_player_message = await interaction.followup.send(f"Loading {self.player_name.value.title()} stats...")
        player_stats_embed = await get_player_stats(self.player_name.value)
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
        last_action_number = self.last_action_numbers.get(game_id, -1)  # Initialize with -1
        await interaction.response.defer(ephemeral=True)

        start_time = datetime.now()
        game_ended = False

        while True:
            try:
                plays, last_action_number = await get_play_by_play(game_id, last_action_number)
                if plays:
                    for play in reversed(plays):  # Iterate over plays in reverse order
                        formatted_play = f"`{play['actionNumber']}` **{play['period']}:{play['clock']}** ({play['actionType']} {play['description']})"
                        await interaction.followup.send(formatted_play)
                    self.last_action_numbers[game_id] = last_action_number
                elif not plays:
                    # Check if 25 minutes have passed since the last play
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
                print(f"Error during interaction: {e}")
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
    url = "https://www.cbssports.com/nba/injuries/"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                soup = BeautifulSoup(await response.text(), 'html.parser')
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
                        embed.set_footer(text=f"Data from CBS Sports | Last Updated: {updated}", icon_url="https://i.imgur.com/9gkhv87.png")
                        return embed
                    else:
                        return discord.Embed(title=f"🏀 Injury Report for {team}", description="No injury information found for this team.", color=0xFF5733)
                else:
                    return discord.Embed(title="❌ Error", description="Team not found in the injury report.", color=0xFF0000)
            else:
                return discord.Embed(title="❌ Error", description="Failed to fetch injury data. Please try again later.", color=0xFF0000)

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