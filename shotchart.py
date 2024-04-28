import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Rectangle, Arc
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
from io import BytesIO
from nba_api.stats.static import players
from nba_api.stats.endpoints import shotchartdetail

def draw_court(ax=None, color='black', lw=2, outer_lines=False):
    """ Function that draws the basketball court lines """
    # If an axes object isn't provided to plot onto, just get current one
    if ax is None:
        ax = plt.gca()

    # Create the various parts of an NBA basketball court

    # Create the basketball hoop
    # Diameter of a hoop is 18" so it has a radius of 9", which is a value
    # of 7.5 in our coordinate system
    hoop = Circle((0, 0), radius=7.5, linewidth=lw, color=color, fill=False)

    # Create backboard
    backboard = Rectangle((-30, -7.5), 60, -1, linewidth=lw, color=color)

    # The paint
    # Create the outer box 0f the paint, width=16ft, height=19ft
    outer_box = Rectangle((-80, -47.5), 160, 190, linewidth=lw, color=color, fill=False)
    # Create the inner box of the paint, width=12ft, height=19ft
    inner_box = Rectangle((-60, -47.5), 120, 190, linewidth=lw, color=color, fill=False)

    # Create free throw top arc
    top_free_throw = Arc((0, 142.5), 120, 120, theta1=0, theta2=180, linewidth=lw, color=color, fill=False)

    # Create free throw bottom arc
    bottom_free_throw = Arc((0, 142.5), 120, 120, theta1=180, theta2=0, linewidth=lw, color=color, linestyle='dashed')

    # Restricted Zone, it is an arc with 4ft radius from center of the hoop
    restricted = Arc((0, 0), 80, 80, theta1=0, theta2=180, linewidth=lw, color=color)

    # Three point line
    # Create the side 3pt lines, they are 14ft long before they begin to arc
    corner_three_a = Rectangle((-220, -47.5), 0, 140, linewidth=lw, color=color)
    corner_three_b = Rectangle((220, -47.5), 0, 140, linewidth=lw, color=color)
    # 3pt arc - center of arc will be the hoop, arc is 23'9" away from hoop
    # I just played around with the theta values until they lined up with the threes
    three_arc = Arc((0, 0), 475, 475, theta1=22, theta2=158, linewidth=lw, color=color)

    # Center Court
    center_outer_arc = Arc((0, 422.5), 120, 120, theta1=180, theta2=0, linewidth=lw, color=color)
    center_inner_arc = Arc((0, 422.5), 40, 40, theta1=180, theta2=0, linewidth=lw, color=color)

    # List of the court elements to be plotted onto the axes
    court_elements = [hoop, backboard, outer_box, inner_box, top_free_throw, bottom_free_throw,
                      restricted, corner_three_a, corner_three_b, three_arc,
                      center_outer_arc, center_inner_arc]

    if outer_lines:
        # Draw the half court line, baseline and sidelines
        outer_lines = Rectangle((-250, -47.5), 500, 470, linewidth=lw, color=color, fill=False)
        court_elements.append(outer_lines)

    # Add the court elements onto the axes
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

async def shot_map(player_name):
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
    ax.scatter(shots.LOC_X, shots.LOC_Y, alpha=0.5, c='blue', marker='o', edgecolors='black', s=100)
    
    #unwanted labels
    ax.set_xlabel('')
    ax.set_ylabel('')

    ax.set_xticks([])
    ax.set_yticks([])

    for spine in ax.spines.values():
        spine.set_visible(False)
        
        
    ax.set_title(f"Shot Chart for {player_name}", fontsize=18)
    ax.set_xlim(-250, 250)
    ax.set_ylim(422.5, -47.5)
    ax.set_xlabel('Court X Coordinate')
    ax.set_ylabel('Court Y Coordinate')
    ax.set_aspect('equal')
    ax.set_facecolor('#eeeeee')

    buf = BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight')
    plt.close(fig)
    buf.seek(0)
    return buf, None
