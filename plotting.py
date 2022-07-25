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
    frames: list[models.Frame], 
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
    with tqdm(total=len(frames), desc = "Drawing frames: ") as progress_bar:
        for i, frame in enumerate(frames):
            f, a = plot_frame(frame, map_name, map_type, dark, show_tiles)
            image_files.append("csgo_tmp/{}.png".format(i))
            f.savefig(image_files[-1], dpi=300, bbox_inches="tight")
            plt.close()
            progress_bar.update()
    images = []
    for file in image_files:
        images.append(imageio.imread(file))
    imageio.mimsave(filename, images)
    shutil.rmtree("csgo_tmp/")
    return True

def plot_frame(frame: models.Frame, map_name: str, map_type: str, dark: bool, show_tiles: bool = True) -> tuple[Figure, Axes]:
    """
    Plots a frame and returns the figure and axes. CTs are blue, Ts are orange, and the bomb is an octagon.
    """
    if show_tiles is True:
        f, a = plot_navigation_mesh(map_name, map_type, dark)
    else:
        f, a = plot.plot_map(map_name, map_type, dark)

    if frame.bomb is not None:
        bomb_x = plot.position_transform(map_name, frame.bomb.x, "x")
        bomb_y = plot.position_transform(map_name, frame.bomb.y, "y")
        a.scatter(x=bomb_x, y=bomb_y, c="yellow", marker="8")

    # TODO: Make smoke/fire circles bigger to be more accurate to how much area they take up in game
    # Trying s = 200 (200% of normal scatter plot point size?)

    for smoke in frame.smokes:
        smoke_x: float = plot.position_transform(map_name, smoke.x, "x")
        smoke_y: float = plot.position_transform(map_name, smoke.y, "y")
        a.scatter(x=smoke_x, y=smoke_y, c="grey", marker=".", edgecolors="white", s=400,)

    for fire in frame.fires:
        fire_x: float = plot.position_transform(map_name, fire.x, "x")
        fire_y: float = plot.position_transform(map_name, fire.y, "y")
        a.scatter(x=fire_x, y=fire_y, c="red", marker=".", s=400)

    color: str
    player_group: list[models.PlayerFrameState]
    for color, player_group in [("cyan", frame.ct.players), ("orange", frame.t.players)]:
        for index, player in enumerate(player_group):
            player_x: float = plot.position_transform(map_name, player.x, "x")
            player_y: float = plot.position_transform(map_name, player.y, "y")

            if player.hp > 0:
                a.scatter(x=player_x, y=player_y, c=color, marker=".")

                # player_view_x is degrees to the left/right (YAW), player_view_y is degrees above/below horizon (PITCH)
                yaw_in_radians = np.deg2rad(360 - player.view_x)
                cartesian_player_view_x: float = np.cos(yaw_in_radians)
                cartesian_player_view_y: float = np.sin(yaw_in_radians)
                # print(player.view_x, cartesian_player_view_x, cartesian_player_view_y)

                # This is to lengthen the vector so it is more easily seen on the map
                VIEW_VECTOR_CONSTANT = 50
                a.arrow(
                    x=player_x, 
                    dx=VIEW_VECTOR_CONSTANT*cartesian_player_view_x, 
                    y=player_y, 
                    dy=VIEW_VECTOR_CONSTANT*cartesian_player_view_y, 
                    color=color, 
                    width=0.00005
                )

                # Raycast test!
                # Draw a point at the first wall the player's view vector hits
                player_area_id: int = nav.find_closest_area(map_name, (player.x, player.y, player.z)).get("areaId", None)
                if player_area_id is not None:
                    final_area_id: int = player_area_id
                    STEP_CONSTANT: int = 1
                    dx: float = cartesian_player_view_x/STEP_CONSTANT
                    dy: float = cartesian_player_view_y/STEP_CONSTANT
                    next_point: tuple[float, float, float] = (player.x + dx, player.y + dy, player.z)
                    do_end_raycast: bool = False
                    iteration_count: int = 0
                    while do_end_raycast is False:
                        iteration_count += 1
                        closest_area_id: int = nav.find_closest_area(map_name, next_point)["areaId"]
                        # If we have gone out of bounds then we probably are in a wall or something so this is our "collision!"
                        if nav.point_in_area(map_name, closest_area_id, next_point) is False:
                            do_end_raycast = True
                        else:
                            final_area_id = closest_area_id
                            next_point = (next_point[0] + dx, next_point[1] + dy, next_point[2])
                    viewmarker_x: float = plot.position_transform(map_name, next_point[0], "x")
                    viewmarker_y: float = plot.position_transform(map_name, next_point[1], "y")
                    a.scatter(x=viewmarker_x, y=viewmarker_y, c=color, marker="2")
                    # print(f"Raycast iteration count: {iteration_count}")

                # Draw lines between this player and other alive players
                for player2 in [p for p in player_group[index:] if p.hp > 0]:
                    player2_x = plot.position_transform(map_name, player2.x, "x")
                    player2_y = plot.position_transform(map_name, player2.y, "y")
                    x_values = [player_x, player2_x]
                    y_values = [player_y, player2_y]
                    a.plot(x_values, y_values, c=color, linestyle="--", linewidth="0.4")

            else:
                a.scatter(x=player_x, y=player_y, c=color, marker="x")

    # Graph time. TODO: Iteratively grow zones of control for each team 
    # (after setting each player's current position as in their control (if there are no enemies in the tile))

    map_graph: nx.Graph = NAV_GRAPHS[map_name]

    ct_player_area_ids: set[int] = {
        nav.find_closest_area(map_name, (player.x, player.y, player.z)).get("areaId", None) for player in frame.ct.players if player.hp > 0
    }
    t_player_area_ids: set[int] = {
        nav.find_closest_area(map_name, (player.x, player.y, player.z)).get("areaId", None) for player in frame.t.players if player.hp > 0
    }
    ct_zone_ids: set[int] = ct_player_area_ids - t_player_area_ids
    t_zone_ids: set[int] = t_player_area_ids - ct_player_area_ids

    # initialize graph with the base positions of each team
    # (where they are standing)
    for node in map_graph.nodes(data=True):
        node_data: dict = node[1]
        node_data["controlling_side"] = None
    for node in map_graph.nodes(data=True):
        area_id: int = node[0]
        node_data: dict = node[1]
        if node_data["areaID"] in ct_zone_ids:
            node_data["controlling_side"] = "CT"
            # Note: to add all immediate neighbors, uncomment this: 
            # for neighbor in map_graph.neighbors(area_id):
            #     neighbor_data: dict = map_graph.nodes[neighbor]
            #     if neighbor_data["controlling_side"] is None:
            #         neighbor_data["controlling_side"] = "CT"
        elif node_data["areaID"] in t_zone_ids:
            node_data["controlling_side"] = "T"
            # Note: to add all immediate neighbors, uncomment this: 
            # for neighbor in map_graph.neighbors(area_id):
            #     neighbor_data: dict = map_graph.nodes[neighbor]
            #     if neighbor_data["controlling_side"] is None:
            #         neighbor_data["controlling_side"] = "T"
        else:
            node_data["controlling_side"] = None
    
    # Spread the zones of control as far as they should
    graph_did_change: bool = True
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
                ct_zone_ids.add(node_data["areaID"])
                # print(f"Zone {node_data['areaID']} is neighbored by 2+ CT zones (formerly controlled by {node_data.get('controlling_side', None)})")
                graph_did_change = True
            elif t_zone_neighbor_count >= 2 and ct_zone_neighbor_count == 0:
                node_data["controlling_side"] = "T"
                t_zone_ids.add(node_data["areaID"])
                # print(f"Zone {node_data['areaID']} is neighbored by 2+ T zones (formerly controlled by {node_data.get('controlling_side', None)})")
                graph_did_change = True

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

        x_se = plot.position_transform(map_name, tile["southEastX"], "x")
        x_nw = plot.position_transform(map_name, tile["northWestX"], "x")
        y_se = plot.position_transform(map_name, tile["southEastY"], "y")
        y_nw = plot.position_transform(map_name, tile["northWestY"], "y")
        width = (x_se - x_nw)
        height = (y_nw - y_se)
        southwest_x = x_nw
        southwest_y = y_se   

        rect = matplotlib.patches.Rectangle((southwest_x,southwest_y), width, height, linewidth=0.4, edgecolor=color, facecolor=color, alpha=0.3)
        a.add_patch(rect)

    return f, a




















# old code




def plot_positions(
    positions: list,
    colors: list,
    markers: list,
    map_name: str,
    map_type: str,
    dark=False,
    show_tiles: bool = True,
    ) -> tuple[Figure, Axes]:
    """
    Plots player positions and draws lines between alive players on the same team

    Args:
        positions (list): List of lists of length 3 ([[x,y,z], ...])
        colors (list): List of colors for each player
        markers (list): List of marker types for each player
        map_name (string): Map to search
        map_type (string): "original" or "simpleradar"
        dark (boolean): Only for use with map_type="simpleradar". Indicates if you want to use the SimpleRadar dark map type

    Returns:
        matplotlib fig and ax
    """
    
    if show_tiles:
        f, a = plot_navigation_mesh(map_name=map_name, map_type=map_type, dark=dark)
    else:
        f, a = plot.plot_map(map_name=map_name, map_type=map_type, dark=dark)

    pcm: list[tuple[tuple[float, float, float], str, str]] = list(zip(positions, colors, markers))
    for index, (p, c, m) in enumerate(pcm):
        x = plot.position_transform(map_name, p[0], "x")
        y = plot.position_transform(map_name, p[1], "y")
        a.scatter(x=x, y=y, c=c, marker=m)
        # If this player is alive draw lines between them and their teammates
        if m != "x":
            for p2, c2, m2 in pcm[index:]:
                # Don't draw lines between players on separate teams
                # And only draw lines between players who are alive
                if c == c2 and m2 != "x":
                    # Draw line between players
                    x2 = plot.position_transform(map_name, p2[0], "x")
                    y2 = plot.position_transform(map_name, p2[1], "y")
                    x_values = [x, x2]
                    y_values = [y, y2]
                    a.plot(x_values, y_values, c=c, linestyle="--", linewidth="0.4")
    # Fill in areas    
    ct_points = [
        (plot.position_transform(map_name, p[0], "x") , plot.position_transform(map_name, p[1], "y")) 
        for p, c, m in pcm if c == "cyan" and m != "x"
    ]
    if len(ct_points) > 2:
        ct_hull = scipy.spatial.ConvexHull(ct_points)
        ct_poly = [ct_points[i] for i in ct_hull.vertices]
        # a.fill([p[0] for p in ct_poly], [p[1] for p in ct_poly], "cyan", alpha=0.3)

        covered_areas: set[int] = set()
        ct_coords: list[tuple[float, float, float]] = [p for p, c, m in pcm if c == "cyan" and m != "x"]
        for idx, p1 in enumerate(ct_coords):
            for p2 in ct_coords[idx+1:]:
                area_ids = get_covered_area(map_name, p1, p2)
                covered_areas.update(area_ids)
        for area in [area for area in NAV[map_name] if area in covered_areas]:
            color = "cyan"
            tile = NAV[map_name][area]

            x_se = plot.position_transform(map_name, tile["southEastX"], "x")
            x_nw = plot.position_transform(map_name, tile["northWestX"], "x")
            y_se = plot.position_transform(map_name, tile["southEastY"], "y")
            y_nw = plot.position_transform(map_name, tile["northWestY"], "y")
            width = (x_se - x_nw)
            height = (y_nw - y_se)
            southwest_x = x_nw
            southwest_y = y_se   

            rect = matplotlib.patches.Rectangle((southwest_x,southwest_y), width, height, linewidth=0.4, edgecolor=color, facecolor=color, alpha=0.3)
            a.add_patch(rect)

    t_points = [(p[0], p[1]) for p, c, m in pcm if c == "orange" and m != "x"]
    if len(t_points) > 2:
        t_hull = scipy.spatial.ConvexHull(t_points)
        t_poly = [t_points[i] for i in t_hull.vertices]
        # a.fill([p[0] for p in t_poly], [p[1] for p in t_poly], "red", alpha=0.3)

        covered_areas: set[int] = set()
        t_coords: list[tuple[float, float, float]] = [p for p, c, m in pcm if c == "orange" and m != "x"]
        for idx, p1 in enumerate(t_coords):
            for p2 in t_coords[idx+1:]:
                area_ids = get_covered_area(map_name, p1, p2)
                covered_areas.update(area_ids)
        for area in [area for area in NAV[map_name] if area in covered_areas]:
            color = "orange"
            tile = NAV[map_name][area]

            x_se = plot.position_transform(map_name, tile["southEastX"], "x")
            x_nw = plot.position_transform(map_name, tile["northWestX"], "x")
            y_se = plot.position_transform(map_name, tile["southEastY"], "y")
            y_nw = plot.position_transform(map_name, tile["northWestY"], "y")
            width = (x_se - x_nw)
            height = (y_nw - y_se)
            southwest_x = x_nw
            southwest_y = y_se   

            rect = matplotlib.patches.Rectangle((southwest_x,southwest_y), width, height, linewidth=0.4, edgecolor=color, facecolor=color, alpha=0.3)
            a.add_patch(rect)

    a.get_xaxis().set_visible(False)
    a.get_yaxis().set_visible(False)

    return f, a

def get_covered_area(map_name: str, point1: tuple[float, float, float], point2: tuple[float, float, float], use_geodesic_distance=False) -> list[int]:
    area1: int = None
    area2: int = None
    for area_id in NAV[map_name].keys():
        if nav.point_in_area(map_name, area_id, point1):
            area1 = area_id
        if nav.point_in_area(map_name, area_id, point2):
            area2 = area_id
    if area1 is None:
        area1 = nav.find_closest_area(map_name, point1)["areaId"]
    if area2 is None:
        area2 = nav.find_closest_area(map_name, point2)["areaId"]
    
    try:
        geodesic_distance = nav.area_distance(map_name=map_name, area_a=area1, area_b=area2, dist_type="geodesic")
        # graph_distance = nav.area_distance(map_name=map_name, area_a=area1, area_b=area2, dist_type="graph")

        # if use_geodesic_distance == True:
        #     distance = nav.area_distance(map_name=map_name, area_a=area1, area_b=area2, dist_type="geodesic")
        # else:
        #     distance = nav.area_distance(map_name=map_name, area_a=area1, area_b=area2, dist_type="graph")

    except nx.NetworkXNoPath:
        print("A player was out of bounds or something. No route could be calculated between them and another player.")
        return []
    
    return geodesic_distance["areas"] # + graph_distance["areas"]