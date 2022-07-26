from awpy.analytics import nav
from awpy.data import NAV
import networkx as nx
import models
import numpy as np
from dataclasses import dataclass, field
from awpy.data import NAV_GRAPHS

def get_perpendicular_vector(vector: np.array) -> np.array:
        """
        Given a vector, returns a vector perpendicular to it
        """
        return np.array([-vector[1], vector[0]])

def get_line_segment_intersection_points(vector_one_endpoints: np.array, vector_two_endpoints: np.array) -> np.array:
    """
    Returns the points where two line segments intersect (assumes they are not parallel)
    Takes the end points of two vectors (they must be the same dimension)
    Taken from https://stackoverflow.com/a/3252222 - thanks!
    """
    if len(vector_one_endpoints) != 2 or len(vector_two_endpoints) != 2:
        raise ValueError("Must provide exactly 2 endpoints for each vector")
    if len(vector_one_endpoints[0]) != len(vector_two_endpoints[0]):
        raise ValueError("Vectors must be of the same dimension")
    da = np.subtract(vector_one_endpoints[1], vector_one_endpoints[0])
    db = np.subtract(vector_two_endpoints[1], vector_two_endpoints[0])
    dp = np.subtract(vector_one_endpoints[0], vector_two_endpoints[0])
    dap = get_perpendicular_vector(da)
    denom = np.dot(dap, db)
    if denom == 0:
        # raise ValueError("Vectors are parallel")
        return np.array([])
    num = np.dot(dap, dp)
    return (num / denom.astype(float))*db + vector_two_endpoints[0]

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

def trace_vision(player: models.PlayerFrameState, frame: models.Frame, map_name: str, fov: int = 90, ray_count: int = 30, step_size: int = 20) -> VisionTraceResults:
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
            if all([x_bounds[0] <= x <= x_bounds[1], y_bounds[0] <= y <= y_bounds[1], z_bounds[0] <= z <= z_bounds[1]]):
                return True

        return False

    for angle in angles_to_trace:
        dx: float = np.cos(angle)*step_size
        dy: float = np.sin(angle)*step_size
        next_point: tuple[float, float, float] = (player.x, player.y, player.z)
        do_end_raycast: bool = False
        iteration_count: int = 0
        nearest_area_id: int = player_area_id
        while do_end_raycast is False:
            iteration_count += 1
            do_end_raycast = True
            if is_point_in_smoke(next_point[0], next_point[1], next_point[2]) is False:
                # TODO: If we can find a way to intelligently decrease the amount of area_ids we test, this will be faster.
                # If we are not in an area then we have gone out of bounds (we probably are in a wall or something so this is our "collision")
                if nav.point_in_area(map_name, nearest_area_id, next_point) is True:
                    do_end_raycast = False
                                        # # TODO: Once we enter an area, use the slope of the line we are tracing to skip to the other end of the area.
                                        # # Skip to the other end of the area
                                        # # get tile entry point
                                        # tile = NAV[map_name][nearest_area_id]
                                        # nw_x: float = tile["northWestX"]
                                        # se_x: float = tile["southEastX"]
                                        # nw_y: float = tile["northWestY"]
                                        # se_y: float = tile["southEastY"]
                                        # SUPER_LARGE_NUMBER: int = 1000000000
                                        # x_lengthen_factor: float = np.cos(angle)*SUPER_LARGE_NUMBER
                                        # y_lengthen_factor: float = np.sin(angle)*SUPER_LARGE_NUMBER
                                        # lengthened_vision_vector_endpoint: tuple[float, float] = (next_point[0] + x_lengthen_factor, next_point[1] + y_lengthen_factor)
                                        # vision_vector_endpoints: np.ndarray = np.array([
                                        #     (next_point[0], next_point[1]), 
                                        #     (lengthened_vision_vector_endpoint[0], lengthened_vision_vector_endpoint[1])
                                        # ])
                                        # tile_perimeter_vector_endpoints: np.ndarray = np.array([
                                        #     [(nw_x, nw_y), (se_x, nw_y)], # NW to NE (y is constant)
                                        #     [(nw_x, nw_y), (nw_x, se_y)], # NW to SW (x is constant)
                                        #     [(nw_x, se_y), (se_x, se_y)], # SW to SE (y is constant)
                                        #     [(se_x, se_y), (se_x, nw_y)], # SE to NE (x is constant)
                                        # ])
                                        # intersection_points = [
                                        #     get_line_segment_intersection_points(vision_vector_endpoints, perimeter_vector_endpoints) 
                                        #     for perimeter_vector_endpoints in tile_perimeter_vector_endpoints
                                        # ]
                                        # end_of_tile_point: tuple[float, float] = None
                                        # # Only check points that are on the tile perimeter
                                        # on_perimeter_points = [
                                        #     p for p in intersection_points if min(nw_x, se_x) <= p[0] <= max(nw_x, se_x) and min(nw_y, se_y) <= p[1] <= max(nw_y, se_y)
                                        # ]
                                        # SUPER_SMALL_NUMBER: int = 0.000001
                                        # for point in on_perimeter_points:
                                        #     step_forward_point = (next_point[0] + dx*SUPER_SMALL_NUMBER, next_point[1] + dy*SUPER_SMALL_NUMBER)
                                        #     current_point = (next_point[0], next_point[1])
                                        #     distance_from_current = np.sqrt((current_point[0] - point[0])**2 + (current_point[1] - point[1])**2)
                                        #     distance_from_step_forward = np.sqrt((step_forward_point[0] - point[0])**2 + (step_forward_point[1] - point[1])**2)
                                        #     if distance_from_step_forward < distance_from_current:
                                        #         end_of_tile_point = point
                                        #         break
                                        # # bug catcher - maybe remove this later
                                        # if end_of_tile_point is None:
                                        #     raise Exception("The SUPER_SMALL_NUMBER was not small enough, it seems.")
                                        # old_point = next_point
                                        # next_point = (end_of_tile_point[0] + dx*SUPER_SMALL_NUMBER, end_of_tile_point[1] + dy*SUPER_SMALL_NUMBER, player.z)
                                        # print(f"Skipped from {old_point} to {next_point}")
                    next_point = (player.x + iteration_count*dx, player.y + iteration_count*dy, player.z)
                else:
                    for area_id in NAV[map_name].keys():
                        if nav.point_in_area(map_name, area_id, next_point) is True:
                            nearest_area_id = area_id
                            do_end_raycast = False
                            next_point = (player.x + iteration_count*dx, player.y + iteration_count*dy, player.z)
                            visible_area_ids.add(area_id)

        trace_results.end_points.append(next_point)
    
    trace_results.visible_area_ids = list(visible_area_ids)

    return trace_results

def calculate_vision_graph(frame: models.Frame, map_name: str) -> tuple[nx.Graph, dict]:
    """
    Returns a map graph with each node containing information about who is viewing it
    Also returns a map of player steam_id to their entire VisionTraceResults object
    """
    map_graph: nx.Graph = NAV_GRAPHS[map_name]
    vision_trace_results: dict[int, VisionTraceResults] = {}

    for node in map_graph.nodes(data=True):
        node_data: dict = node[1]
        previous_covered_by_set: set[int] = node_data.get("covered_by", None) or set()
        node_data["covered_by"] = set()
        node_data["previously_covered_by"] = previous_covered_by_set

    for player in [p for p in frame.ct.players + frame.t.players if p.hp > 0]:
        trace_results: VisionTraceResults = trace_vision(player=player, frame=frame, map_name=map_name)
        vision_trace_results[player.steam_id] = trace_results

        for visible_area_id in trace_results.visible_area_ids:
            for node in map_graph.nodes(data=True):
                area_id: int = node[0]
                if visible_area_id == area_id:
                    node_data: dict = node[1]
                    node_data["covered_by"].add(player.steam_id)

    return (map_graph, vision_trace_results)

def grow_controlled_areas(frame: models.Frame, map_graph: nx.Graph) -> nx.Graph:
    """
    TODO: Iteratively grow zones of control for each team 
    (after setting each player's current position as in their control (if there are no enemies in the tile))

    TODO: Figure out controlled area growth rules.
    Idea: maybe if a tile has a neighbor that is a color, and it has no path to the opposite color, make it that color.
    Idea: if a tile is viewed by a side, mark it as viewed by that player.
      if that tile is then viewed by a player from the enemy team, mark it as viewed by that player.
      if a player dies, mark every tile that they were viewing as no longer viewed
      
    each tile has a "covered_by" attribute, which is a list of players that are viewing it.

    initialize graph with the base positions of each team
    (where they are standing)
    """

    alive_ct_player_ids = [p.steam_id for p in frame.ct.players if p.hp > 0]
    alive_t_player_ids = [p.steam_id for p in frame.t.players if p.hp > 0]

    for node in map_graph.nodes(data=True):
        node_data: dict = node[1]
        node_data["controlling_side"] = None
        ct_count = 0
        t_count = 0
        # Commenting this out to disable vision persisting across frames
        # If this tile hasn't been updated this frame (i.e. viewed) then just use the information from last frame
        # if len(node_data["covered_by"]) == 0:
        #     node_data["covered_by"] = node_data["previously_covered_by"]
        covered_by_set: set[int] = node_data["covered_by"]
        for player in covered_by_set:
            if player in alive_ct_player_ids:
                ct_count += 1
            elif player in alive_t_player_ids:
                t_count += 1
        if ct_count > t_count:
            node_data["controlling_side"] = "CT"
        elif t_count > ct_count:
            node_data["controlling_side"] = "T"
        elif ct_count == t_count:
            node_data["controlling_side"] = None
    
    # # Spread the zones of control as far as they should
    # # TODO: This is not super great (it's wrong a lot)
    # graph_did_change: bool = True
    # graph_did_change = False # TODO: Re-enable this
    # while graph_did_change:
    #     graph_did_change = False
    #     for node in map_graph.nodes(data=True):
    #         area_id: int = node[0]
    #         node_data: dict = node[1]
    #         ct_zone_neighbor_count: int = 0
    #         t_zone_neighbor_count: int = 0
    #         if node_data["controlling_side"] is not None:
    #             continue
    #         for neighbor in map_graph.neighbors(area_id):
    #             neighbor_data: dict = map_graph.nodes[neighbor]
    #             if neighbor_data["controlling_side"] == "CT":
    #                 ct_zone_neighbor_count += 1
    #             elif neighbor_data["controlling_side"] == "T":
    #                 t_zone_neighbor_count += 1
    #         if ct_zone_neighbor_count >= 2 and t_zone_neighbor_count == 0:
    #             node_data["controlling_side"] = "CT"
    #             ct_covered_area_ids.add(node_data["areaID"])
    #             # print(f"Zone {node_data['areaID']} is neighbored by 2+ CT zones (formerly controlled by {node_data.get('controlling_side', None)})")
    #             graph_did_change = True
    #         elif t_zone_neighbor_count >= 2 and ct_zone_neighbor_count == 0:
    #             node_data["controlling_side"] = "T"
    #             t_covered_area_ids.add(node_data["areaID"])
    #             # print(f"Zone {node_data['areaID']} is neighbored by 2+ T zones (formerly controlled by {node_data.get('controlling_side', None)})")
    #             graph_did_change = True

    return map_graph
