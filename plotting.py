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
    frames: list[dict], 
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
        for i, f in enumerate(frames):
            positions = []
            colors = []
            markers = []
            # Plot bomb
            # Thanks to https://github.com/pablonieto0981 for adding this code!
            if f["bomb"]:
                colors.append("orange")
                markers.append("8")
                pos = (
                    f["bomb"]["x"],
                    f["bomb"]["y"],
                    f["bomb"]["z"],
                )
                positions.append(pos)
            else:
                pass
            # Plot players
            for side in ["ct", "t"]:
                for p in f[side]["players"]:
                    if side == "ct":
                        colors.append("cyan")
                    else:
                        colors.append("red")
                    if p["hp"] == 0:
                        markers.append("x")
                    else:
                        markers.append(".")
                    pos = (
                        # plot.position_transform(map_name, p["x"], "x"),
                        # plot.position_transform(map_name, p["y"], "y"),
                        p["x"],
                        p["y"],
                        p["z"]
                    )
                    positions.append(pos)
            f, a = plot_positions(
                positions=positions,
                colors=colors,
                markers=markers,
                map_name=map_name,
                map_type=map_type,
                dark=dark,
                show_tiles=show_tiles
            )
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

    t_points = [(p[0], p[1]) for p, c, m in pcm if c == "red" and m != "x"]
    if len(t_points) > 2:
        t_hull = scipy.spatial.ConvexHull(t_points)
        t_poly = [t_points[i] for i in t_hull.vertices]
        # a.fill([p[0] for p in t_poly], [p[1] for p in t_poly], "red", alpha=0.3)

        covered_areas: set[int] = set()
        t_coords: list[tuple[float, float, float]] = [p for p, c, m in pcm if c == "red" and m != "x"]
        for idx, p1 in enumerate(t_coords):
            for p2 in t_coords[idx+1:]:
                area_ids = get_covered_area(map_name, p1, p2)
                covered_areas.update(area_ids)
        for area in [area for area in NAV[map_name] if area in covered_areas]:
            color = "red"
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