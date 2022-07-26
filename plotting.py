import os
import shutil
import imageio
import matplotlib
from matplotlib.figure import Figure
from matplotlib.axes import Axes
import matplotlib.pyplot as plt
from awpy.visualization import plot
from awpy.data import NAV
from awpy.analytics import nav
import networkx as nx
import scipy.spatial
from tqdm import tqdm
import models
import numpy as np
from awpy.data import NAV_GRAPHS
import mathing

def plot_navigation_mesh(map_name: str, map_type: str, dark: bool) -> tuple[Figure, Axes]:
    """
    Plots the map's navigation mesh
    """

    f: Figure
    ax: Axes

    f, ax = plot.plot_map(map_name = map_name, map_type = map_type, dark = dark)

    for a in NAV[map_name]:
        tile = NAV[map_name][a]
        x_se = plot.position_transform(map_name, tile["southEastX"], "x")
        x_nw = plot.position_transform(map_name, tile["northWestX"], "x")
        y_se = plot.position_transform(map_name, tile["southEastY"], "y")
        y_nw = plot.position_transform(map_name, tile["northWestY"], "y")
        width = (x_se - x_nw)
        height = (y_nw - y_se)
        southwest_x = x_nw
        southwest_y = y_se
        rect = matplotlib.patches.Rectangle((southwest_x,southwest_y), width, height, linewidth=0.2, edgecolor="yellow", facecolor="None")
        ax.add_patch(rect)

    ax.get_xaxis().set_visible(False)
    ax.get_yaxis().set_visible(False)

    return f, ax

def plot_rounds(demo_file_data, output_file_directory: str) -> None:
    """
    Given a parsed demo file, plot all rounds of the demo and save it to a file
    Output file name shouldn't contain extensions
    """
    total_rounds = len(demo_file_data["gameRounds"])
    for index, round in enumerate(demo_file_data["gameRounds"]):
        # TODO: Make sure that the output is sent to the right place
        print(f"Creating .gif for round {index}/{total_rounds}:")
        plot_round(f"{output_file_directory}/round{index}.gif", round["frames"], map_name=demo_file_data["mapName"])

def plot_first_round(demo_file_data, output_file_name: str) -> None:
    """
    Given a parsed demo file, plot the first round of the demo and save it to a file
    """
    first_round_data = demo_file_data["gameRounds"][0]["frames"]
    plot_round(f"{output_file_name}.gif", first_round_data, map_name=demo_file_data["mapName"])

def plot_round(
    filename: str, 
    round: models.Round, 
    map_name: str, 
    map_type: str, 
    dark: bool = False, 
    show_tiles: bool = False
    ) -> tuple[Figure, Axes]:
    """Plots a round and saves as a .gif. CTs are blue, Ts are orange, and the bomb is an octagon. Only use untransformed coordinates.

    Args:
        filename (string): Filename to save the gif
        frames (list): List of frames from a parsed demo
        markers (list): List of marker types for each player
        map_name (string): Map to search
        map_type (string): "original" or "simpleradar"
        dark (boolean): Only for use with map_type="simpleradar". Indicates if you want to use the SimpleRadar dark map type

    Returns:
        matplotlib fig and ax, saves .gif
    """
    if os.path.isdir("csgo_tmp"):
        shutil.rmtree("csgo_tmp/")
    os.mkdir("csgo_tmp")
    image_files = []
    frames = round.frames
    grenade_throwers: dict[tuple[float, float, float], str] = {
        (g.grenade_x, g.grenade_y, g.grenade_z): g.thrower_side for g in round.grenades
    }
    with tqdm(total=len(frames), desc = "Drawing frames: ") as progress_bar:
        for i, frame in enumerate(frames):
            f, a = plot_frame(frame, grenade_throwers, map_name, map_type, dark, show_tiles)
            image_files.append("csgo_tmp/{}.png".format(i))
            f.savefig(image_files[-1], dpi=300, bbox_inches="tight")
            plt.close()
            progress_bar.update()
    images = []
    for file in image_files:
        images.append(imageio.imread(file))
    imageio.mimsave(filename, images, fps=1)
    shutil.rmtree("csgo_tmp/")
    return True

def plot_frame(frame: models.Frame, grenade_throwers: dict[int, str], previous_frame_graph: nx.Graph | None, map_name: str, map_type: str, dark: bool, show_tiles: bool = True) -> tuple[Figure, Axes, nx.Graph]:
    """
    Plots a frame and returns the figure, axes, and the map graph (containing area controlled information).
    CTs are blue, Ts are orange, and the bomb is an octagon.
    """
    if show_tiles is True:
        f, a = plot_navigation_mesh(map_name, map_type, dark)
    else:
        f, a = plot.plot_map(map_name, map_type, dark)

    x_transform = lambda x: plot.position_transform(map_name, x, "x")
    y_transform = lambda y: plot.position_transform(map_name, y, "y")

    if frame.bomb is not None:
        bomb_x = x_transform(frame.bomb.x)
        bomb_y = y_transform(frame.bomb.y)
        a.scatter(x=bomb_x, y=bomb_y, c="yellow", marker="8")

    ct_visible_area_ids: set[int] = set()
    t_visible_area_ids: set[int] = set()

    map_graph: nx.Graph = previous_frame_graph or nx.Graph()

    team: models.TeamFrameState
    color: str
    visible_area_ids: set[int]
    for team, color in [(frame.ct, "xkcd:azure"), (frame.t, "xkcd:orange")]:
        player_group: list[models.PlayerFrameState] = team.players
        for index, player in enumerate(player_group):

            player_x: float = x_transform(player.x)
            player_y: float = y_transform(player.y)

            if player.hp <= 0:
                a.scatter(x=player_x, y=player_y, c=color, marker="x")
                continue

            a.scatter(x=player_x, y=player_y, c=color, marker=".")
            # Draw lines between this player and other alive players
            for player2 in [p for p in player_group[index:] if p.hp > 0]:
                player2_x = x_transform(player2.x)
                player2_y = y_transform(player2.y)
                x_values = [player_x, player2_x]
                y_values = [player_y, player2_y]
                a.plot(x_values, y_values, c=color, linestyle="dotted", linewidth="0.4")

            # Get information about where the player is looking
            trace_results: mathing.VisionTraceResults = mathing.trace_vision(player, frame, map_name)
            aim_end_point = trace_results.end_points[0]
            visible_area_ids.update(trace_results.visible_area_ids)

            # Draw a line to where the player is aiming
            a.scatter(x=x_transform(aim_end_point[0]), y=y_transform(aim_end_point[1]), c=color, marker="2")
            a.plot([player_x, x_transform(aim_end_point[0])], [player_y, y_transform(aim_end_point[1])], c=color, linestyle="--", linewidth=0.5)

            # Draw lines for every view vector cast
            for end_point in trace_results.end_points[1:]:
                view_vector_end_point_x = x_transform(end_point[0])
                view_vector_end_point_y = y_transform(end_point[1])
                x_values = [player_x, view_vector_end_point_x]
                y_values = [player_y, view_vector_end_point_y]
                # a.scatter(x=end_point[0], y=end_point[1], c=color, marker="2")
                a.plot(x_values, y_values, c=color, linestyle="dotted", linewidth="0.4", alpha=0.2)

    # Graph time. TODO: Iteratively grow zones of control for each team 
    # (after setting each player's current position as in their control (if there are no enemies in the tile))

    map_graph: nx.Graph = NAV_GRAPHS[map_name]

    # ct_occupied_area_ids: set[int] = {
    #     nav.find_closest_area(map_name, (player.x, player.y, player.z)).get("areaId", None) for player in frame.ct.players if player.hp > 0
    # }
    # t_occupied_area_ids: set[int] = {
    #     nav.find_closest_area(map_name, (player.x, player.y, player.z)).get("areaId", None) for player in frame.t.players if player.hp > 0
    # }
    # ct_covered_area_ids: set[int] = ct_occupied_area_ids.difference(t_occupied_area_ids).union(ct_visible_area_ids)
    # t_covered_area_ids: set[int] = t_occupied_area_ids.difference(ct_occupied_area_ids).union(t_visible_area_ids)
    ct_covered_area_ids: set[int] = ct_visible_area_ids
    t_covered_area_ids: set[int] = t_visible_area_ids

    # TODO: Figure out controlled area growth rules.
    # Idea: maybe if a tile has a neighbor that is a color, and it has no path to the opposite color, make it that color.
    # Idea: if a tile is viewed by a side, mark it as viewed by that player.
    #   if that tile is then viewed by a player from the enemy team, mark it as viewed by that player.
    #   if a player dies, mark every tile that they were viewing as no longer viewed
    #   
    # each tile has a "covered_by" attribute, which is a list of players that are viewing it.

    # initialize graph with the base positions of each team
    # (where they are standing)
    for node in map_graph.nodes(data=True):
        node_data: dict = node[1]
        node_data["controlling_side"] = None
    for node in map_graph.nodes(data=True):
        area_id: int = node[0]
        node_data: dict = node[1]
        if node_data["areaID"] in ct_covered_area_ids:
            node_data["controlling_side"] = "CT"
            # Note: to add all immediate neighbors, uncomment this: 
            # for neighbor in map_graph.neighbors(area_id):
            #     neighbor_data: dict = map_graph.nodes[neighbor]
            #     if neighbor_data["controlling_side"] is None:
            #         neighbor_data["controlling_side"] = "CT"
        elif node_data["areaID"] in t_covered_area_ids:
            node_data["controlling_side"] = "T"
            # Note: to add all immediate neighbors, uncomment this: 
            # for neighbor in map_graph.neighbors(area_id):
            #     neighbor_data: dict = map_graph.nodes[neighbor]
            #     if neighbor_data["controlling_side"] is None:
            #         neighbor_data["controlling_side"] = "T"
        else:
            node_data["controlling_side"] = None
    
    # Spread the zones of control as far as they should
    # TODO: This is not super great (it's wrong a lot)
    graph_did_change: bool = True
    graph_did_change = False # TODO: Re-enable this
    while graph_did_change:
        graph_did_change = False
        for node in map_graph.nodes(data=True):
            area_id: int = node[0]
            node_data: dict = node[1]
            ct_zone_neighbor_count: int = 0
            t_zone_neighbor_count: int = 0
            if node_data["controlling_side"] is not None:
                continue
            for neighbor in map_graph.neighbors(area_id):
                neighbor_data: dict = map_graph.nodes[neighbor]
                if neighbor_data["controlling_side"] == "CT":
                    ct_zone_neighbor_count += 1
                elif neighbor_data["controlling_side"] == "T":
                    t_zone_neighbor_count += 1
            if ct_zone_neighbor_count >= 2 and t_zone_neighbor_count == 0:
                node_data["controlling_side"] = "CT"
                ct_covered_area_ids.add(node_data["areaID"])
                # print(f"Zone {node_data['areaID']} is neighbored by 2+ CT zones (formerly controlled by {node_data.get('controlling_side', None)})")
                graph_did_change = True
            elif t_zone_neighbor_count >= 2 and ct_zone_neighbor_count == 0:
                node_data["controlling_side"] = "T"
                t_covered_area_ids.add(node_data["areaID"])
                # print(f"Zone {node_data['areaID']} is neighbored by 2+ T zones (formerly controlled by {node_data.get('controlling_side', None)})")
                graph_did_change = True

    # Color tiles!
    for node in map_graph.nodes(data=True):
        node_data: dict = node[1]
        controlling_side = node_data.get("controlling_side", None)
        if controlling_side is None:
            continue
        elif controlling_side == "CT":
            color = "cyan"
        elif controlling_side == "T":
            color = "orange"

        area_id: int = node_data["areaID"]
        tile = NAV[map_name][area_id]

        x_se = x_transform(tile["southEastX"])
        x_nw = x_transform(tile["northWestX"])
        y_se = y_transform(tile["southEastY"])
        y_nw = y_transform(tile["northWestY"])
        width = (x_se - x_nw)
        height = (y_nw - y_se)
        southwest_x = x_nw
        southwest_y = y_se   

        rect = matplotlib.patches.Rectangle((southwest_x,southwest_y), width, height, linewidth=0.4, edgecolor=color, facecolor=color, alpha=0.3)
        a.add_patch(rect)

    # TODO: Resize markers to match how big they are in game if necessary

    def get_thrower_of_closest_grenade(x: float, y: float, z: float) -> str:
        """
        Given a grenade's x, y, z coordinates, find the thrower of the closest grenade
        """
        closest_grenade_id = min(grenade_throwers, key=lambda g: (g[0] - x)**2 + (g[1] - y)**2 + (g[2] - z)**2)
        return grenade_throwers[closest_grenade_id]

    for smoke in frame.smokes:
        smoke_x: float = plot.position_transform(map_name, smoke.x, "x")
        smoke_y: float = plot.position_transform(map_name, smoke.y, "y")
        owner = get_thrower_of_closest_grenade(smoke.x, smoke.y, smoke.z)
        outline_color = "xkcd:azure" if owner == "CT" else "xkcd:orange" if owner == "T" else "black"
        a.scatter(x=smoke_x, y=smoke_y, c="grey", marker=".", edgecolors=outline_color, s=400,)

    for fire in frame.fires:
        fire_x: float = plot.position_transform(map_name, fire.x, "x")
        fire_y: float = plot.position_transform(map_name, fire.y, "y")
        owner = get_thrower_of_closest_grenade(fire.x, fire.y, fire.z)
        outline_color = "xkcd:azure" if owner == "CT" else "xkcd:orange" if owner == "T" else "black"
        a.scatter(x=fire_x, y=fire_y, c="red", marker=".", edgecolors=outline_color, s=400)

    return f, a