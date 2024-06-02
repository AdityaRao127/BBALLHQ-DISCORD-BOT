import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Rectangle, Arc
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
from io import BytesIO
from nba_api.stats.static import players
from nba_api.stats.endpoints import shotchartdetail
import datetime as dt
import numpy as np
import seaborn as sns
import tempfile
import os

current_year = dt.datetime.now().year
if dt.datetime.now().month < 10:
    current_year = current_year - 1
    
    
def draw_court(ax=None, color='black', lw=2, outer_lines=False):
    """ Function that draws the basketball court lines """
    # If an axes object isn't provided to plot onto, just get current one
    if ax is None:
        ax = plt.gca()

    # bball court outline
    hoop = Circle((0, 0), radius=7.5, linewidth=lw, color=color, fill=False)

   
    backboard = Rectangle((-30, -7.5), 60, -1, linewidth=lw, color=color)

    outer_box = Rectangle((-80, -47.5), 160, 190, linewidth=lw, color=color, fill=False)

    inner_box = Rectangle((-60, -47.5), 120, 190, linewidth=lw, color=color, fill=False)


    top_free_throw = Arc((0, 142.5), 120, 120, theta1=0, theta2=180, linewidth=lw, color=color, fill=False)

    
    bottom_free_throw = Arc((0, 142.5), 120, 120, theta1=180, theta2=0, linewidth=lw, color=color, linestyle='dashed')


    restricted = Arc((0, 0), 80, 80, theta1=0, theta2=180, linewidth=lw, color=color)

    corner_three_a = Rectangle((-220, -47.5), 0, 140, linewidth=lw, color=color)
    corner_three_b = Rectangle((220, -47.5), 0, 140, linewidth=lw, color=color)

    three_arc = Arc((0, 0), 475, 475, theta1=22, theta2=158, linewidth=lw, color=color)


    center_outer_arc = Arc((0, 422.5), 120, 120, theta1=180, theta2=0, linewidth=lw, color=color)
    center_inner_arc = Arc((0, 422.5), 40, 40, theta1=180, theta2=0, linewidth=lw, color=color)

    court_elements = [hoop, backboard, outer_box, inner_box, top_free_throw, bottom_free_throw,
                      restricted, corner_three_a, corner_three_b, three_arc,
                      center_outer_arc, center_inner_arc]

    if outer_lines:
        outer_lines = Rectangle((-250, -47.5), 500, 470, linewidth=lw, color=color, fill=False)
        court_elements.append(outer_lines)

    # Add court elements
    for element in court_elements:
        ax.add_patch(element)

    return ax

async def get_player_id(player_name):
    normalized_input_name = player_name.strip().lower()
    player_dict = players.get_players()
    player = [p for p in player_dict if p['full_name'].lower() == normalized_input_name]
    if not player:
        parts = normalized_input_name.split()
        normalized_input_name = ', '.join(parts[::-1])
        player = [p for p in player_dict if p['full_name'].lower() == normalized_input_name]
    if player:
        return player[0]['id']
    return "Player not found."

async def shot_map(player_name, chart_type='regular'):
    player_id = await get_player_id(player_name)
    if isinstance(player_id, str):  
        return None, player_id

    shot_chart = shotchartdetail.ShotChartDetail(
        team_id=0,
        player_id=player_id,
        context_measure_simple='FGA'
    )
    shots = shot_chart.get_data_frames()[0]

    fig, ax = plt.subplots(figsize=(12, 11))
    draw_court(ax, outer_lines=True)

    if chart_type == 'regular':
        ax.scatter(shots.LOC_X, shots.LOC_Y, alpha=0.5, c='blue', marker='o', edgecolors='black', s=100)
    elif chart_type == 'heatmap':
        sns.kdeplot(x=shots.LOC_X, y=shots.LOC_Y, fill=True, alpha=0.5, cmap="YlOrRd", bw_adjust=0.5, ax=ax)
        draw_court(ax, color="black", lw=1, outer_lines=True)

    # limits
    ax.set_xlim(-250, 250)
    ax.set_ylim(-47.5, 422.5)

    # Remove unwanted axes/labels
    ax.set_xlabel('')
    ax.set_ylabel('')
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_visible(False)

    ax.set_title(f"{player_name.upper()} Shotchart {current_year}-{current_year+1}", fontsize=20)
    ax.set_facecolor('#eeeeee')
    ax.set_aspect('equal')

    temp_dir = tempfile.mkdtemp()
    file_path = os.path.join(temp_dir, 'shot_chart.png')
    plt.savefig(file_path, bbox_inches='tight')
    plt.close(fig)
    
    return file_path, None