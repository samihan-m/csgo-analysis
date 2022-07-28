import parsing
import models
import timelining
import plotting
import mathing
from tqdm import tqdm
import networkx as nx
import tkinter as tk
from tkinter import filedialog
import os
import csv
from dataclasses import fields
import shutil

def extract_demo_data() -> None:
    """
    Run the main 'extract data' routine in console mode
    """

    root = tk.Tk()
    # To open file dialog in a new window on top of everything else instead of behind everything else
    root.wm_attributes('-topmost', 1)
    root.withdraw()

    print("Select the .dem file from which you would like to extract the data (see new window):")
    input_file_path = filedialog.askopenfilename(title="Open a .dem file",filetypes=[("demo files", "*.dem")])
    if input_file_path == "":
        print("No file selected, cancelling.")
        return
    print("Extracting data from file: " + input_file_path)

    print("Select the directory in which you would like to save the .csv and image files (see new window):")
    output_directory = filedialog.askdirectory(initialdir=os.getcwd(), title="Choose where you want the .csv and .gif files to be saved:")
    if output_directory == "":
        print("No directory selected, cancelling.")
        return
    print("Saving data to directory: " + output_directory)

    if os.path.isdir(output_directory) is False:
        print("Output directory does not exist. Creating directory.")
        os.mkdir(output_directory)

    print("Beginning data extraction...")
    print(f"Loading demo file at {input_file_path}, please wait...")
    parsed_demo_data = parsing.parse_demo_file(input_file_path)
    demo: models.Demo = models.deserialize_demo_data(parsed_demo_data)
    print("Loaded demo file.")
    print("Creating event timeline.")
    timeline: timelining.Timeline = timelining.create_timeline(demo)
    print("Demo analyzed, timeline created.")

    events_file_name: str = f"{output_directory}/events.csv"
    print(f"Saving event timeline to {events_file_name}")
    with open(events_file_name, "w") as file:
        writer = csv.writer(file)
        all_fields: list[str] = []
        for event in timeline.events:
            all_fields.extend([field.name for field in fields(event)])
        unique_fields = list(dict.fromkeys(all_fields))
        writer.writerow([field for field in unique_fields])
        for event in timeline.events:
            writer.writerow([getattr(event, field, None) for field in unique_fields])
    print("Event timeline saved.")

    event_descriptions_file_name: str = f"{output_directory}/event_descriptions.csv"
    print(f"Saving event descriptions to {event_descriptions_file_name}")
    with open(event_descriptions_file_name, "w") as file:
        writer = csv.writer(file)
        writer.writerow(["tick", "name", "description"])
        for event in timeline.events:
            writer.writerow([event.tick, event.__class__.__name__, str(event)])
    print("Event descriptions saved.")

    print("Calculating frame-specific data and saving frame images for every round in the game.")
    print("This might take a while. Go do something else while you wait!")
    rounds_folder: str = f"{output_directory}/round_visualizations"
    if os.path.isdir(rounds_folder) is False:
        print("Round visualizations folder does not exist. Creating folder.")
        os.mkdir(rounds_folder)
    print(f"Saving to {rounds_folder}")
    # Moved this dictionary out here because now it will track controlled_area_sizes for the whole game instead of one round
    controlled_area_sizes: dict[int, dict[str, float]] = {}
    for round_index, round in enumerate(demo.game_rounds):
        round_number = round_index + 1
        vision_graphs: list[nx.Graph] = []
        vision_traces: list[dict[int, mathing.VisionTraceResults]] = []
        with tqdm(total=len(round.frames), desc=f"Calculating frame vision information for round {round_index+1}/{len(demo.game_rounds)}: ") as progress_bar:
            for frame in round.frames:
                vision_graph: nx.Graph
                trace_results: dict[int, mathing.VisionTraceResults]
                vision_graph, trace_results = mathing.calculate_vision_graph(frame=frame, map_name=demo.map_name)
                vision_graph = mathing.grow_controlled_areas(frame=frame, map_graph=vision_graph)
                controlled_area_sizes[frame.tick] = mathing.calculate_controlled_area_sizes(map_graph=vision_graph, map_name=demo.map_name)
                vision_graphs.append(vision_graph)
                vision_traces.append(trace_results)
                progress_bar.update()
        folder_name = f"{rounds_folder}/round_{round_number}"
        if os.path.isdir(folder_name):
            print(f"{folder_name} already exists. Emptying it's contents.")
            shutil.rmtree(f"{folder_name}/")
        os.mkdir(folder_name)
        plotting.plot_round(
            image_directory=folder_name, 
            round_number=round_number,
            round=round, 
            vision_graphs=vision_graphs,
            vision_traces=vision_traces,
            map_name=demo.map_name,
        )
        print("Saved round images.")

        area_controlled_file_name: str = f"{output_directory}/area_controlled.csv"
        print(f"Saving area controlled data to {area_controlled_file_name}")
        with open(output_directory + "/area_controlled.csv", "w") as file:
            writer = csv.writer(file)
            writer.writerow(["tick", "CT", "T"])
            for tick, controlled_area_size_dict in controlled_area_sizes.items():
                writer.writerow([tick, controlled_area_size_dict["CT"], controlled_area_size_dict["T"]])
        print("Area controlled data saved.")

    # print("Extracting player location information, please wait...")
    # player_information = parsing.extract_player_information(parsed_demo_data)
    # print("Extracted player location information.")
    # print(f"Saving to {output_file_path}")
    # parsing.write_player_information_to_csv(player_information, output_directory+"/player_locations.csv")
    # print("Wrote player location information to output file.")

    # print("Extracting team area controlled information, please wait...")
    # area_data = mathing.get_area_controlled_information_for_game(parsed_demo_data)
    # print("Extracted team area controlled information.")
    # print("Select to where you would like the output .csv file to save (see new window):")
    # output_file_path = get_csv_output_file_name()
    # print(f"Saving to {output_file_path}")
    # parsing.write_area_controlled_information_to_csv(area_data, output_file_path)
    # print("Wrote team area controlled information to output file.")

    # do_save_gifs: bool = None
    # while do_save_gifs is None:
    #     print("Would you like to save .gifs of each round visualizing player locations? (This will take some time.) (Y/N)")
    #     user_input = input("Enter your choice: ").upper()
    #     if user_input not in ["Y", "N"]:
    #         print("Invalid input. Please try again.")
    #         continue
    #     if user_input == "Y":
    #         do_save_gifs = True
    #     if user_input == "N":
    #         do_save_gifs = False
    # if do_save_gifs is True:
    #     print("Select the directory where you would like the .gif files to be saved (see new window):")
    #     gif_output_directory = get_gif_output_directory()
    #     print(f"Saving .gifs to {gif_output_directory}")
    #     plotting.plot_rounds(parsed_demo_data, gif_output_directory)
    #     print("Saved .gifs.")

    print(f"Done saving the game! Check the {output_directory} folder for the output files.")
    
def main() -> None:
    """
    Launch CLI version of the program
    """
    print("Welcome to the CS:GO Demo File Player Data Extractor!")
    do_quit: bool = False
    while do_quit is False:
        print("Select an option:")
        print("""1. Extract data from a .dem file, creating .csv files for game events and team area controlled, 
        as well as .gifs for visualizing the area controlled by each team.""")
        print("Q. Quit")
        user_input = input("Enter your choice: ").upper()
        if user_input not in ["1", "Q"]:
            print("Invalid input. Please try again.")
            continue
        if user_input == "1":
            extract_demo_data()
        if user_input == "Q":
            do_quit = True
            input("Closing. Press ENTER to continue.")
            return

if __name__ == "__main__":
    main()