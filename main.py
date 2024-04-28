from discord.ext import commands
import os
from dotenv import load_dotenv
import discord
from stats import get_player_stats, get_team_stats 
from shotchart import shot_map

# Load the environment variable
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

# Initialize the bot
bot = commands.Bot(command_prefix='!', intents=discord.Intents.all())


class OptionsDropdown(discord.ui.Select):
    def __init__(self):
        options=[
            discord.SelectOption(label='Live NBA Scores', description='Live scores from nba games 🏀'),
            discord.SelectOption(label = 'Play-by-play', description='NBA play-by-play of the game 📢'),
            discord.SelectOption(label='Player Stats', description='Player stats📊'),
            discord.SelectOption(label ='Team Stats', description='Team_stats📊'),
            discord.SelectOption(label ='Shot Chart', description='Shot chart of players and teams 📈'),
            discord.SelectOption(label='Machine Learning Prediction', description='Simple ML-based predictions of a game🤖'),
            discord.SelectOption(label='Latest News', description='Reliable news sources 📰'),
        
        ]
        super().__init__(placeholder='Choose an option', options=options, min_values=1, max_values=1)

    async def callback(self, interaction: discord.Interaction):
        if self.values[0] == "Live NBA Scores":
           interaction.response.send_message("Unknown option selected, please try again.")
        elif self.values[0] == "Play-by-play":
           interaction.response.send_message("Unknown option selected, please try again.")
        elif self.values[0] == "Player Stats":
             await interaction.response.send_modal(PlayerStats())
        elif self.values[0] == "Team Stats":
             await interaction.response.send_modal(TeamStats())
        elif self.values[0] == "Shot Chart":
               await interaction.response.send_modal(ShotChart())
        elif self.values[0] == "Machine Learning Prediction":
            interaction.response.send_message("Unknown option selected, please try again.")
        elif self.values[0] == "Latest News":
          interaction.response.send_message("Unknown option selected, please try again.")
        else:
            await interaction.response.send_message("Unknown option selected, please try again.")

# get inputs for the functions
class PlayerStats(discord.ui.Modal, title="Player Stats"):
    # Text input for player name
    player_name = discord.ui.TextInput(label="Enter the NBA player's name:")

    async def on_submit(self, interaction: discord.Interaction):
        # Handle the player stats lookup when the modal form is submitted
        player_stats = await get_player_stats(self.player_name.value)
        await interaction.response.send_message(player_stats)
        
class TeamStats(discord.ui.Modal, title="Team Stats"):
    # Text input for player name
    team_name = discord.ui.TextInput(label="Enter an NBA team name:")

    async def on_submit(self, interaction: discord.Interaction):
        # Handle the player stats lookup when the modal form is submitted
        await interaction.response.defer()
        loading_message = await interaction.followup.send("Loading team stats...")
        team_stats = await get_team_stats(self.team_name.value)
        await loading_message.edit(content=team_stats)
        
class ShotChart(discord.ui.Modal, title="Shot Chart"):
    # Text input for player name
    player_chart_name = discord.ui.TextInput(label="Enter the NBA player's name:")

    async def on_submit(self, interaction: discord.Interaction):
        # Defer
        await interaction.response.defer()
        # Generate the shot chart
        buffer, error = await shot_map(self.player_chart_name.value)
        new_loading_message = await interaction.followup.send("Loading team stats...")
        if error is not None:
            await interaction.followup.send(error)
            return
        
        file = discord.File(buffer, filename="shot_chart.png")
        await new_loading_message.edit(interaction.followup.send(file=file))

class DropdownView(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.add_item(OptionsDropdown())

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
    await ctx.send('Hello, I an NBA bot. Type !nba to get started!')
    


# Event to confirm the bot is online
@bot.event
async def on_ready():
    print(f'{bot.user.name} has connected to Discord!')

bot.run(TOKEN)
