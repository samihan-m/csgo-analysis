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
    imageio.mimsave(filename, images)
    shutil.rmtree("csgo_tmp/")
    return True

def plot_frame(frame: models.Frame, grenade_throwers: dict[int, str], map_name: str, map_type: str, dark: bool, show_tiles: bool = True) -> tuple[Figure, Axes]:
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

    # TODO: If possible, add a CT highlight to things spawned by CT's and a T highlight to things spawned by T's
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
        outline_color = "cyan" if owner == "CT" else "orange" if owner == "T" else "black"
        a.scatter(x=smoke_x, y=smoke_y, c="grey", marker=".", edgecolors=outline_color, s=400,)

    for fire in frame.fires:
        fire_x: float = plot.position_transform(map_name, fire.x, "x")
        fire_y: float = plot.position_transform(map_name, fire.y, "y")
        owner = get_thrower_of_closest_grenade(fire.x, fire.y, fire.z)
        outline_color = "cyan" if owner == "CT" else "orange" if owner == "T" else "black"
        a.scatter(x=fire_x, y=fire_y, c="red", marker=".", edgecolors=outline_color, s=400)

    ct_visible_areas: set[int] = set()
    t_visible_areas: set[int] = set()

    color: str
    player_group: list[models.PlayerFrameState]
    for color, player_group in [("cyan", frame.ct.players), ("orange", frame.t.players)]:
        for index, player in enumerate(player_group):
            player_x: float = plot.position_transform(map_name, player.x, "x")
            player_y: float = plot.position_transform(map_name, player.y, "y")

            if player.hp > 0:
                a.scatter(x=player_x, y=player_y, c=color, marker=".")

                # TODO: Ray cast issues: 
                # Sometimes they end too early (like sitting behind the car on dust2 shouldn't count as completely obstructing vision)
                # They will not be blocked by smokes
                # Does not include areas behind somebody that are "covered" because there is no way something can get behind them
                # (e.g. top left corner of the dust2 gif)
                
                # TODO: Add more raycast lines from a player
                # assume each player has a 60 degree FOV and cast out lines 30 degrees +- from the player's view vector

                # TODO: Faster raycast method
                # Make steps way larger, and if we go out of bounds, then 'revert' and decrease step size and try again
                # Minimum step size will be 1*np.cos(yaw), 1*np.sin(yaw)

                # Raycast test!
                # Draw a point at the first wall the player's view vector hits
                player_area_id: int = nav.find_closest_area(map_name, (player.x, player.y, player.z)).get("areaId", None)
                if player_area_id is not None:
                    final_area_id: int = player_area_id
                    STEP_CONSTANT: int = 0.01
                    yaw_in_radians = np.deg2rad(player.view_x)
                    dx: float = np.cos(yaw_in_radians)/STEP_CONSTANT
                    dy: float = np.sin(yaw_in_radians)/STEP_CONSTANT
                    next_point: tuple[float, float, float] = (player.x, player.y, player.z)
                    do_end_raycast: bool = False
                    iteration_count: int = 0
                    while do_end_raycast is False:
                        iteration_count += 1
                        do_end_raycast = True
                        for area_id in NAV[map_name].keys():
                            # TODO: Add check for if the point is within a smoke
                            # If we have gone out of bounds then we probably are in a wall or something so this is our "collision!"
                            if nav.point_in_area(map_name, area_id, next_point):
                                do_end_raycast = False
                                next_point = (player.x + iteration_count*dx, player.y + iteration_count*dy, player.z)
                                if color == "cyan":
                                    ct_visible_areas.add(area_id)
                                elif color == "orange":
                                    t_visible_areas.add(area_id)
                                final_area_id = area_id

                    viewmarker_x: float = plot.position_transform(map_name, next_point[0], "x")
                    viewmarker_y: float = plot.position_transform(map_name, next_point[1], "y")

                    a.plot([player_x, viewmarker_x], [player_y, viewmarker_y], c=color, linestyle="--", linewidth=0.5)

                    a.scatter(x=viewmarker_x, y=viewmarker_y, c=color, marker="2")
                    # print(f"Raycast iteration count: {iteration_count}")

                # Draw lines between this player and other alive players
                for player2 in [p for p in player_group[index:] if p.hp > 0]:
                    player2_x = plot.position_transform(map_name, player2.x, "x")
                    player2_y = plot.position_transform(map_name, player2.y, "y")
                    x_values = [player_x, player2_x]
                    y_values = [player_y, player2_y]
                    a.plot(x_values, y_values, c=color, linestyle="dotted", linewidth="0.4")

            else:
                a.scatter(x=player_x, y=player_y, c=color, marker="x")

    # Graph time. TODO: Iteratively grow zones of control for each team 
    # (after setting each player's current position as in their control (if there are no enemies in the tile))

    map_graph: nx.Graph = NAV_GRAPHS[map_name]

    ct_occupied_area_ids: set[int] = {
        nav.find_closest_area(map_name, (player.x, player.y, player.z)).get("areaId", None) for player in frame.ct.players if player.hp > 0
    }
    t_occupied_area_ids: set[int] = {
        nav.find_closest_area(map_name, (player.x, player.y, player.z)).get("areaId", None) for player in frame.t.players if player.hp > 0
    }
    ct_covered_area_ids: set[int] = ct_occupied_area_ids.difference(t_occupied_area_ids).union(ct_visible_areas)
    t_covered_area_ids: set[int] = t_occupied_area_ids.difference(ct_occupied_area_ids).union(t_visible_areas)

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
                ct_covered_area_ids.add(node_data["areaID"])
                # print(f"Zone {node_data['areaID']} is neighbored by 2+ CT zones (formerly controlled by {node_data.get('controlling_side', None)})")
                graph_did_change = True
            elif t_zone_neighbor_count >= 2 and ct_zone_neighbor_count == 0:
                node_data["controlling_side"] = "T"
                t_covered_area_ids.add(node_data["areaID"])
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