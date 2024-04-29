from nba_api.stats.endpoints import playbyplayv3
from nba_api.stats.endpoints import scoreboardv2
from nba_api.live.nba.endpoints import scoreboard
from datetime import datetime
from dateutil import parser, tz
import pytz 
from nba_api.live.nba.endpoints import boxscore

async def get_play_by_play(game_id):
    try:
        pbp = playbyplayv3.PlayByPlayV3(game_id=game_id)
        df = pbp.get_data_frames()
        if df and not df[0].empty:
            plays = df[0]
            formatted_data = '\n'.join(f"{play['PCTIMESTRING']} - {play['HOMEDESCRIPTION'] if play['HOMEDESCRIPTION'] else play['VISITORDESCRIPTION']}" for index, play in plays.iterrows())
            return formatted_data
        else:
            return "No play-by-play data available."
    except Exception as e:
        return f"Error retrieving play-by-play: {str(e)}"



async def fetch_live_games():
    try:
        board = scoreboard.ScoreBoard()
        
        games = board.games.get_dict()
        upcoming_games = []
        ongoing_games = []
        finished_games = []
        
        # Current time
        now = datetime.now(tz=pytz.utc)

        for game in games:
            # local timezone
            gameTimeLTZ = parser.parse(game["gameTimeUTC"]).replace(tzinfo=pytz.utc).astimezone(pytz.timezone('America/Los_Angeles'))
            
            home_team = game['homeTeam']['teamName']
            away_team = game['awayTeam']['teamName']
            home_score = game['homeTeam']['score']
            away_score = game['awayTeam']['score']
            game_status = game['gameStatus']
            game_id = game['gameId']

            time_display = gameTimeLTZ.strftime('%I:%M %p %Z')

            if game_status == 1:  # Game is upcoming
                upcoming_games.append(f"**{away_team} vs. {home_team}** starts at {time_display}")
            elif game_status == 2:  # Game is ongoing
                ongoing_games.append(f"**{away_team} vs. {home_team}** @ {time_display}\nCurrent score: {away_team} `{away_score}` - `{home_score}` {home_team}\n")
            elif game_status == 3:  # Game is completed
                if home_score > away_score:
                    winner = f"{home_team} win"
                else:
                    winner = f"{away_team} win"
                finished_games.append(f"{away_team} vs. {home_team}\nScore: ||{away_score} - {home_score}, ***{winner}***||\n")

        # Date formatting
        date_today = datetime.now()
        formatted_date = date_today.strftime("%B %d")
        summary = f"**NBA GAMES FOR {formatted_date} ({date_today.month}/{date_today.day})**\n"

        # Append each category to summary
        if upcoming_games:
            summary += "\n**Upcoming games:**\n" + "\n".join(upcoming_games) + "\n"
        if ongoing_games:
            summary += "\n**Ongoing games:**\n" + "\n".join(ongoing_games) + "\n"
        if finished_games:
            summary += "\n**Completed games:**\n" + "\n".join(finished_games) + "\n"
        else:
            summary += "\nNo games today.\n"
        
        return summary

    except Exception as e:
        return f"Error fetching live games: {str(e)}"

def ordinal(n): #  get date suffix
    if 10 <= n % 100 <= 20:
        suffix = 'th'
    else:
        suffix = {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')
    return str(n) + suffix