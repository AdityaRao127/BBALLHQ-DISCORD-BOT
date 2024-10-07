import discord
from nba_api.stats.static import players
from nba_api.stats.static import teams
from nba_api.stats.endpoints import playercareerstats, playerdashboardbyyearoveryear, teamgamelog, teamdashboardbygeneralsplits, teamdashboardbyshootingsplits
import datetime as dt
import pandas as pd
import asyncio
import time
from discord.ext import commands
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

current_year = dt.datetime.now().year
if dt.datetime.now().month < 10:
    current_year = current_year - 1

async def get_player_stats(player_name):
    logger.debug(f"Fetching stats for player: {player_name}")
    # Find player by name
    player_dict = players.get_players()
    player = [p for p in player_dict if p['full_name'].lower() == player_name.lower()]
    if player:
        player_id = player[0]['id']
        logger.debug(f"Player ID: {player_id}")

        logger.debug("Fetching career stats")
        career = playercareerstats.PlayerCareerStats(player_id=player_id)
        career_df = career.get_data_frames()[0]
        time.sleep(3)  # Increased sleep time

        logger.debug("Fetching advanced stats")
        advanced_stats = playerdashboardbyyearoveryear.PlayerDashboardByYearOverYear(player_id=player_id)
        advanced_df = advanced_stats.get_data_frames()[1]
        time.sleep(3)  # Increased sleep time

        logger.debug("Processing stats data")
        latest_season_reg = career_df.iloc[-1]
        latest_season_advanced = advanced_df.iloc[-1]

        # Create a Discord embed
        embed = discord.Embed(
            title=f"**{player_name.title()}**",
            color=0x0099ff  # Blue color
        )

        # Add author, thumbnail, fields, and footer to the embed
        embed.set_author(name="NBA Stats Bot", icon_url="https://i.imgur.com/axLm3p6.jpeg")
        embed.set_thumbnail(url="https://cdn.nba.com/headshots/nba/latest/1040x760/{player_id}.png") #fix

        # Extract season year
        season_id_parts = latest_season_reg['SEASON_ID'].split('-')
        season_year = int(season_id_parts[1]) + 1
        embed.description = f"**Regular Season Stats for {player_name.title()}, {season_id_parts[0]}-{season_year}**"

        # Add regular season stats fields
        embed.add_field(name="Points Per Game", value=f"{latest_season_reg['PTS'] / latest_season_reg['GP']:.1f}", inline=False)
        embed.add_field(name="Assists Per Game", value=f"{latest_season_reg['AST'] / latest_season_reg['GP']:.1f}", inline=False)
        embed.add_field(name="Rebounds Per Game", value=f"{latest_season_reg['REB'] / latest_season_reg['GP']:.1f}", inline=False)
        embed.add_field(name="Steals Per Game", value=f"{latest_season_reg['STL'] / latest_season_reg['GP']:.1f}", inline=False)
        embed.add_field(name="Blocks Per Game", value=f"{latest_season_reg['BLK'] / latest_season_reg['GP']:.1f}", inline=False)

        # Add shooting percentages field
        embed.add_field(name="Shooting Percentages", value=f"FG%: {latest_season_reg['FG_PCT'] * 100:.3f}%\nFT%: {latest_season_reg['FT_PCT'] * 100:.3f}%\n3P%: {latest_season_reg['FG3_PCT'] * 100:.3f}%", inline=False)

        # Add advanced stats fields
        embed.add_field(name="Turnovers Per Game", value=f"{latest_season_reg['TOV']}", inline=False)
        embed.add_field(name="Win Shares", value=f"{latest_season_advanced['W']}", inline=False)
        embed.add_field(name="Offensive Rebounds Per Game", value=f"{latest_season_advanced['OREB']}", inline=False)
        embed.add_field(name="Plus/Minus (Season)", value=f"{latest_season_advanced['PLUS_MINUS']}", inline=False)

        #embed.set_footer(text="Data provided by NBA API")

        logger.debug("Player stats embed created successfully")
        return embed
    else:
        logger.warning(f"Player not found: {player_name}")
        embed = discord.Embed(
            title="Error",
            description="Spell the player's name correctly",
            color=0xff0000  # Red color
        )
        return embed

async def get_team_stats(team_name):
    logger.debug(f"Fetching stats for team: {team_name}")
    # Find team by name
    team_dict = teams.get_teams()
    team = [t for t in team_dict if t['full_name'].lower() == team_name.lower()]

    if team:
        team_id = team[0]['id']
        logger.debug(f"Team ID: {team_id}")

        logger.debug("Fetching team dashboard stats")
        team_stats = teamdashboardbygeneralsplits.TeamDashboardByGeneralSplits(team_id=team_id)
        time.sleep(3)  # Increased sleep time

        logger.debug("Fetching team shooting splits")
        team_ranks = teamdashboardbyshootingsplits.TeamDashboardByShootingSplits(team_id=team_id)
        time.sleep(3)  # Increased sleep time
        
        logger.debug("Processing team stats data")
        team_df = team_stats.get_data_frames()[0]  # Assuming first DataFrame contains seasonal stats
        # other_df = team_ranks.get_data_frames()[0]
        
        stats = {
            "Wins": team_df['W'][0],
            "Losses": team_df['L'][0],
            "Win Percentage": round(team_df['W_PCT'][0] * 100, 1),
            "Field Goal Percentage": round(team_df['FG_PCT'][0] * 100, 1),
            "Free Throw Percentage": round(team_df['FT_PCT'][0] * 100, 1),
            "Three-Point Percentage": round(team_df['FG3_PCT'][0] * 100, 1),
        }
        
        stats_message = (
            f"**{team_name.title()} Regular Season Stats for {current_year}-{current_year+1} Season**\n"
            f"Wins: {stats['Wins']}\n"
            f"Losses: {stats['Losses']}\n"
            f"Win Percentage: {stats['Win Percentage']}%\n"
            f"Field Goal Percentage: {stats['Field Goal Percentage']}%\n"
            f"Free Throw Percentage: {stats['Free Throw Percentage']}%\n"
            f"Three-Point Percentage: {stats['Three-Point Percentage']}%\n"
            f"\n"
            f"**Other Stats**\n"
            f"Turnovers: {team_df['TOV'][0]}\n"
            f"Plus/Minus: {team_df['PLUS_MINUS'][0]}\n"
            #f"Rest Days: {team_df['TEAM_DAYS_REST_RANGE'][0]}\n"  did not work some reason
            f"\n"
            f"**Rankings: Work in progress**\n"
            #f"Field Goal Percentage Rank: {other_df['FG_PCT_RANK'][0]}\n"
            #f"Three-Point Percentage Rank: {other_df['FG3_PCT_RANK'][0]}\n"
            #f"THree-Point Field Goals Made Rank: {other_df['FG3M_RANK'][0]}\n"
            #f"Turnover Rank: {team_df['TOV_RANK'][0]}\n" dont work
           # f"Plus/Minus Rank: {team_df['PLUS_MINUS_RANK'][0]}\n"

    
        )
        
        
        logger.debug("Team stats message created successfully")
        return stats_message
    else:
        logger.warning(f"Team not found: {team_name}")
        return "Spell the team name correctly"