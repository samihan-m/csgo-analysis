from awpy.parser import DemoParser
from dataclasses import fields
import csv
import logging
import plotting
import mathing
from mathing import PlayerState, TeamArea


def parse_demo_file(demo_file_name: str) -> dict:
    """
    Given a demo file name, parse it and return the data
    """
    logging.debug("Reached inside of  parse_demo_file")
    # 128 parse_rate ideally matches with the 128 ticks per second of the demo file to mean player position is polled every second
    p = DemoParser(demofile=demo_file_name, parse_rate=128, parse_frames=True)
    logging.debug("Constructed DemoParser")
    data = p.parse()
    logging.debug("Parsed demo file")
    return data

def extract_player_information(demo_file_data) -> list:
    """
    Given a parsed demo file, extract player states from it and return a list of PlayerState information
    """

    player_information: list[PlayerState] = []

    data = demo_file_data

    for game_round_index in range(0, len(data["gameRounds"])):
        frames = data["gameRounds"][game_round_index]["frames"]
        for frame in frames:
            for team in ["ct", "t"]:
                for player in frame[team]["players"]:
                    player_information.append(PlayerState(game_round_index, player["name"], team, player["x"], player["y"], player["z"]))

    return player_information

def write_player_information_to_csv(player_information: list[PlayerState], csv_file_name: str) -> None:
    """
    Provided a list of player information, write it to a csv file
    """
    with open(csv_file_name, "w") as output_file:
        writer = csv.writer(output_file)
        writer.writerow([class_field.name for class_field in fields(PlayerState)])
        for state_entry in player_information:
            writer.writerow([getattr(state_entry, field_name) for field_name in [class_field.name for class_field in fields(PlayerState)]])

def write_area_controlled_information_to_csv(controlled_area_information: dict, csv_file_name: str) -> None:
    with open(csv_file_name, "w") as output_file:
        writer = csv.writer(output_file)
        writer.writerow([class_field.name for class_field in fields(TeamArea)])
        for area_entry in controlled_area_information:
            writer.writerow([getattr(area_entry, field_name) for field_name in [class_field.name for class_field in fields(TeamArea)]])

def main():
    demo_file_name = r"D:/Samihan/Documents/Programming/Python Projects/CSGO Demo Parsing/demos/cloud9-vs-outsiders-m1-dust2.dem"
    print(f"Parsing {demo_file_name}")
    data = parse_demo_file(demo_file_name)
    print(data.keys())

    print(f"Plotting rounds for {demo_file_name}")

    # plotting.plot_rounds(data, "cloud9-vs-outsiders-m1-dust2")
    # plotting.plot_first_round(data, "testing-fill-2")

    first_frame = data["gameRounds"][0]["frames"][0]

    # print(first_frame)

    # outer_points = mathing.get_outer_team_points(first_frame)
    # print(mathing.get_covered_area_between_points(first_frame, data["mapName"]))

    # print("Processing full game now")
    # area_data = mathing.get_area_controlled_information_for_game(data)
    # write_area_controlled_information_to_csv(area_data, "cloud9-vs-outsiders-m1-dust2-controlled-area.csv")
    # print("Wrote data.")
    

if __name__ == "__main__":
    main()
