from nba_api.stats.static import players
from nba_api.stats.endpoints import playercareerstats, playerdashboardbyyearoveryear
import datetime as dt
current_year = dt.datetime.now().year


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
        
        latest_season_reg = career_df.iloc[-1]

        latest_season_advanced = advanced_df.iloc[-1]
        
        stats = {
            "PPG": round(latest_season_reg['PTS'] / latest_season_reg['GP'], 1), 
            "APG": round(latest_season_reg['AST'] / latest_season_reg['GP'], 1),  
            "RPG": round(latest_season_reg['REB'] / latest_season_reg['GP'], 1),
            "SPG": round(latest_season_reg['STL'] / latest_season_reg['GP'], 1),  
            "BPG": round(latest_season_reg['BLK'] / latest_season_reg['GP'], 1), 
            "FG%": round(latest_season_reg['FG_PCT'] * 100, 1)  
        }

        # Prepare structured regular stats data
        regular_stats_message = (
            f"**Regular Stats for {player_name}**\n"
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
        return "Spell the player's name correctly!"