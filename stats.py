from nba_api.stats.static import players
from nba_api.stats.static import teams
from nba_api.stats.endpoints import playercareerstats, playerdashboardbyyearoveryear, teamgamelog, teamdashboardbygeneralsplits, teamdashboardbyshootingsplits
import datetime as dt
import pandas as pd
import asyncio
import time
current_year = dt.datetime.now().year
if dt.datetime.now().month < 10:
    current_year = current_year - 1

async def get_player_stats(player_name):
    # Find player by name
    player_dict = players.get_players()
    player = [p for p in player_dict if p['full_name'].lower() == player_name.lower()]
    if player:
        player_id = player[0]['id']
        career = playercareerstats.PlayerCareerStats(player_id=player_id)
        career_df = career.get_data_frames()[0]
        
        # Fetch advanced stats
        advanced_stats = playerdashboardbyyearoveryear.PlayerDashboardByYearOverYear(player_id=player_id)
        advanced_df = advanced_stats.get_data_frames()[1]
        
        time.sleep(0.600)
        latest_season_reg = career_df.iloc[-1]

        latest_season_advanced = advanced_df.iloc[-1]

        # Prepare structured regular stats data
        regular_stats_message = (
            f"**Regular Season Stats for {player_name.title()}, {current_year}-{current_year+1}**\n"
            f"Points Per Game : {latest_season_reg['PTS'] / latest_season_reg['GP']:.1f}\n"
            f"Assists Per Game: {latest_season_reg['AST'] / latest_season_reg['GP']:.1f}\n"
            f"Rebounds Per Game: {latest_season_reg['REB'] / latest_season_reg['GP']:.1f}\n"
            f"Steals Per Game: {latest_season_reg['STL'] / latest_season_reg['GP']:.1f}\n"
            f"Blocks Per Game: {latest_season_reg['BLK'] / latest_season_reg['GP']:.1f}\n"
            f"\n"
            f"**Shooting Percentages**\n"
            f"Field Goal Percentage: {latest_season_reg['FG_PCT'] * 100:.3f}%\n"
            f"Free Throw Percentage: {latest_season_reg['FT_PCT'] * 100:.3f}%\n"
            f"Three-Point Percentage: {latest_season_reg['FG3_PCT'] * 100:.3f}%\n"
        )

        # Prepare structured advanced stats data
        advanced_stats_message = (
            f"**Other Stats**\n"
            f"Turnovers Per Game: {latest_season_reg['TOV']}\n"
            f"Win Shares: {latest_season_advanced['W']}\n"
            f"Offensive Rebounds Per Game: {latest_season_advanced['OREB']}\n"
            f"Plus/Minus (Season): {latest_season_advanced['PLUS_MINUS']}\n"
        )

        return regular_stats_message + "\n" + advanced_stats_message
    else:
        return "Spell the player's name correctly"
    
async def get_team_stats(team_name):
    # Find team by name
    team_dict = teams.get_teams()
    team = [t for t in team_dict if t['full_name'].lower() == team_name.lower()]

    if team:
        team_id = team[0]['id']
        # Fetch team dashboard stats
        team_stats = teamdashboardbygeneralsplits.TeamDashboardByGeneralSplits(team_id=team_id)
        team_ranks = teamdashboardbyshootingsplits.TeamDashboardByShootingSplits(team_id=team_id)
        
        time.sleep(0.600)
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
        
        
        return stats_message
    else:
        return "Spell the team name correctly"