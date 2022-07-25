from awpy.analytics import nav
from scipy.spatial import ConvexHull
from dataclasses_json import dataclass_json
from awpy.data import NAV
import networkx as nx
from tqdm import tqdm

import models
import numpy as np
from dataclasses import dataclass, field

@dataclass
class VisionTraceResults:
    """
    Contains information about the results of a vision ray cast.
    The first angle in angled_traced is a straight line forward from where the player is looking.
    (and the first value in end_points is the first wall the player's vision ray encounters.)
    """
    angles_traced: list[float] = field(default_factory=list) # In degrees
    end_points: list[tuple[float, float, float]] = field(default_factory=list)
    visible_area_ids: list[int] = field(default_factory=list)

def trace_vision(player: models.PlayerFrameState, frame: models.Frame, map_name: str, fov: int = 90, ray_count: int = 30, step_size: int = 50) -> VisionTraceResults:
    """
    Given a player position and view angle, trace multiple lines in their vision cone. Returns a VisionTraceResults object.
    fov is (in degrees) how large the "vision cone" is.
    ray_count is the number of lines to draw, the more lines, the more accurate the results but the slower the function.
    step_size is how far along each line we check to see if the line has collided with something - 
        the more steps, the more accurate the results but the slower the function.
    """
    trace_results: VisionTraceResults = VisionTraceResults()

    visible_area_ids: set[int] = set()

    player_area_id: int = nav.find_closest_area(map_name, (player.x, player.y, player.z)).get("areaId", None)
    if player_area_id is None:
        return list(visible_area_ids)
    visible_area_ids.add(player_area_id)

    angles_to_trace: list[float] = [player.view_x]
    angles_to_trace.extend([player.view_x + i for i in range(int(-fov/2), int(fov/2 + 1), int(fov/ray_count))])

    trace_results.angles_traced = angles_to_trace

    angles_to_trace = np.deg2rad(angles_to_trace)

    def is_point_in_smoke(x: float, y: float, z: float) -> bool:
        """
        Given a point, returns if it is in a smoke or not
        """
        SMOKE_RADIUS: int = 144 # Taken from CS:GO wiki
        for smoke in frame.smokes:
            x_bounds: list[float] = [smoke.x - SMOKE_RADIUS, smoke.x + SMOKE_RADIUS]
            y_bounds: list[float] = [smoke.y - SMOKE_RADIUS, smoke.y + SMOKE_RADIUS]
            z_bounds: list[float] = [smoke.z - SMOKE_RADIUS, smoke.z + SMOKE_RADIUS]
            if any([x_bounds[0] <= x <= x_bounds[1], y_bounds[0] <= y <= y_bounds[1], z_bounds[0] <= z <= z_bounds[1]]):
                return True

        return False

    for angle in angles_to_trace:
        dx: float = np.cos(angle)*step_size
        dy: float = np.sin(angle)*step_size
        next_point: tuple[float, float, float] = (player.x, player.y, player.z)
        do_end_raycast: bool = False
        iteration_count: int = 0
        while do_end_raycast is False:
            iteration_count += 1
            do_end_raycast = True
            for area_id in NAV[map_name].keys():
                # If we have gone out of bounds then we probably are in a wall or something so this is our "collision!"
                if (
                    nav.point_in_area(map_name, area_id, next_point) is True and
                    is_point_in_smoke(next_point[0], next_point[1], next_point[2]) is False
                ):
                    do_end_raycast = False
                    next_point = (player.x + iteration_count*dx, player.y + iteration_count*dy, player.z)
                    visible_area_ids.add(area_id)

        trace_results.end_points.append(next_point)
    
    trace_results.visible_area_ids = list(visible_area_ids)

    return trace_results

# def get_team_covered_areas(team: models.TeamFrameState, frame: models.Frame, map_name: str) -> list[int]:
#     """
#     Returns a list of ids for 'covered' areas 
#     An area is covered if a player is inside it or if it is in their vision
#     """
#     covered_areas: set[int] = {}
    
#     for player in team.players:
#         if player.hp <= 0:
#             continue
#         trace_results: dict = trace_vision(player, frame, map_name)
#         covered_areas.update(trace_results["visible_area_ids"])

#     return list(covered_areas)






















@dataclass_json
@dataclass
class PlayerState:
    """
    Contains information about a player's state during a demo frame
    """
    x: float
    y: float
    z: float
    round_index: int = None
    player_name: str = None
    team: str = None

@dataclass_json
@dataclass
class TeamArea:
    """
    Contains information about a team's controlled area
    """
    frame_index: int
    team: str
    controlled_area: float
    controlled_volume: float


def get_outer_team_points(game_frame: dict) -> dict[str, list[list]]:
    """
    Given a game frame, get the outer points of the area controlled by each team and return them
    """
    points = {
        "ct": [],
        "t": [],
    }
    ct_players: list[PlayerState] = []
    for player in game_frame["ct"]["players"]:
        ct_players.append(PlayerState(x=player["x"], y=player["y"], z=player["z"], team="ct"))
    points["ct"] = [[player.x, player.y, player.z] for player in ct_players]
    if len(ct_players) > 2:
        ct_points = [[player.x, player.y, player.z] for player in ct_players]
        ct_hull = ConvexHull(ct_points)
        points["ct"] = [ct_players[i] for i in ct_hull.vertices]

    t_players: list[PlayerState] = []
    for player in game_frame["t"]["players"]:
        t_players.append(PlayerState(x=player["x"], y=player["y"], z=player["z"], team="t"))
    points["t"] = [[player.x, player.y, player.z] for player in t_players]
    if len(t_players) > 2:
        t_points = [[player.x, player.y, player.z] for player in t_players]
        t_hull = ConvexHull(t_points)
        points["t"] = [t_players[i] for i in t_hull.vertices]

    return points

def get_area_coords(map_name: str, area_id: int) -> list[float]:
    """
    Given an area_id, get the area coordinates
    """
    area: dict = NAV[map_name].get(area_id, None)
    if area is None:
        raise KeyError("AreaId not found")
    return [
        # (area["northWestX"], area["northWestY"], area["northWestZ"]),
        # (area["southEastX"], area["southEastY"], area["southEastZ"]),
        (area["northWestX"], area["northWestY"], area["northWestZ"]), (area["southEastX"], area["southEastY"], area["southEastZ"]),
    ]

def get_area_size(map_name:str, area_id: int) -> float:
    """
    Given an areaId, get the area size
    """
    area: dict = NAV[map_name].get(area_id, None)
    if area is None:
        raise KeyError("AreaId not found")
    print("Area statistics: ", area)
    x: float = abs(area["northWestX"] - area["southEastX"])
    y: float = abs(area["northWestY"] - area["southEastY"])
    z: float = abs(area["northWestZ"] - area["southEastZ"])
    return x * y * z

def get_covered_area_between_points(game_frame: dict, map_name: str) -> dict[str, float]:
    """
    Given a game frame, calculate the amount of area covered by each team
    """
    area_covered = {
        "ct": {
            "area": 0.0,
            "volume": 0.0,
        }, 
        "t": {
            "area": 0.0,
            "volume": 0.0,
        }
    }
    # points = get_outer_team_points(game_frame)
    points = {
        "ct": [PlayerState(x=player["x"], y=player["y"], z=player["z"], team="ct") for player in game_frame["ct"]["players"]],
        "t": [PlayerState(x=player["x"], y=player["y"], z=player["z"], team="t") for player in game_frame["t"]["players"]],
    }

    for team in points:
        team_positions = points[team]

        if len(team_positions) == 0:
            continue
        if len(team_positions) == 1:
            coords = [points[0].x, points[0].y, points[0].z]
            area = nav.find_closest_area(map_name, coords)
            area_covered[team] = get_area_size(map_name, area)
            continue

        covered_area_ids: set[int] = set()
        # Calculate distances between every pair of points
        for index, point1 in enumerate(team_positions):
            coords_one = [point1.x, point1.y, point1.z]
            area_one = nav.find_closest_area(map_name, coords_one)
            for point2 in team_positions[index:]:
                coords_two = [point2.x, point2.y, point2.z]
                area_two = nav.find_closest_area(map_name, coords_two)
                try:
                    distance = nav.area_distance(map_name, area_one["areaId"], area_two["areaId"])
                except nx.NetworkXNoPath as e:
                    print(e)
                    print("Continuing...")
                    continue
                if distance["distance"] > 0:
                    for area_id in distance["areas"][1:]:
                        covered_area_ids.add(area_id)

        # print(covered_area_ids)
        covered_area_coords: list[float] = []
        for area_id in covered_area_ids:
            area_coords = get_area_coords(map_name, area_id)
            covered_area_coords.extend(area_coords)
        # print(covered_area_coords)
        if len(covered_area_coords) < 2:
            print("This frame does not have a 3D area for which to calculate the volume. Skipping it.")
            continue
        try:
            area_hull = ConvexHull(covered_area_coords)
        except Exception as e:
            print(e)
            print("Continuing..")
            continue

        # print(area_hull.vertices)
        
        area_covered[team]["area"] = area_hull.area
        area_covered[team]["volume"] = area_hull.volume

    return area_covered

def get_area_controlled_information_for_game(demo_file_data) -> list[TeamArea]:
    total_frames: int = 0
    for round_index in range(0, len(demo_file_data["gameRounds"])):
        for frame_index in range(0, len(demo_file_data["gameRounds"][round_index]["frames"])):
            total_frames += 1

    with tqdm(total=total_frames, desc="Calculating bounding box area and volume for each game frame...") as progress_bar:
        frame_counter = 0
        area_data: list[TeamArea] = []
        for round_index in range(0, len(demo_file_data["gameRounds"])):
            for frame_index in range(0, len(demo_file_data["gameRounds"][round_index]["frames"])):
                frame = demo_file_data["gameRounds"][round_index]["frames"][frame_index]
                covered_area_info: dict = get_covered_area_between_points(frame, demo_file_data["mapName"])
                ct_area_info = TeamArea(frame_counter, "ct", covered_area_info["ct"]["area"], covered_area_info["ct"]["volume"])
                t_area_info = TeamArea(frame_counter, "t", covered_area_info["t"]["area"], covered_area_info["t"]["volume"])
                area_data.append(ct_area_info)
                area_data.append(t_area_info)
                frame_counter += 1
                progress_bar.update()
                # print("Processed frame", frame_counter)
    return area_data