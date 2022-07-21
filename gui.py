import logging
import parsing
import plotting
import mathing
import tkinter as tk
from tkinter import filedialog
import os

def get_demo_file_name() -> str:
    """
    Returns the path to the demo file provided by the user
    """
    file_path = filedialog.askopenfilename(title="Open a .dem file",filetypes=[("demo files", "*.dem")])
    return file_path

def get_csv_output_file_name() -> str:
    """
    Returns the path to an output file provided by the user
    """
    file_path = filedialog.asksaveasfilename(title="Choose where to save the .csv file", filetypes=[("csv files", "*.csv")])
    if file_path.endswith(".csv") is False:
        file_path += ".csv"
    return file_path

def get_gif_output_directory() -> str:
    """
    Returns the path to an output directory provided by the user
    """
    file_path = filedialog.askdirectory(initialdir=os.getcwd(), title="Choose where you want the .gif files to be saved:")
    # TODO: Handle cases where user doesn't enter anything
    return file_path

# Taken from https://stackoverflow.com/questions/3352918/how-to-center-a-window-on-the-screen-in-tkinter
def center(win):
    """
    centers a tkinter window
    :param win: the main window or Toplevel window to center
    """
    win.update_idletasks()
    width = win.winfo_width()
    frm_width = win.winfo_rootx() - win.winfo_x()
    win_width = width + 2 * frm_width
    height = win.winfo_height()
    titlebar_height = win.winfo_rooty() - win.winfo_y()
    win_height = height + titlebar_height + frm_width
    x = win.winfo_screenwidth() // 2 - win_width // 2
    y = win.winfo_screenheight() // 2 - win_height // 2
    win.geometry('{}x{}+{}+{}'.format(width, height, x, y))
    win.deiconify()

def run() -> None:
    """
    Run through the entire process of asking player for a demo file, extracting info from it, and saving it as a .csv.
    """

    try:
        logging.debug("Asking user for demo file name\n")
        input_file_path = get_demo_file_name()
        if input_file_path == "":
            return
        logging.debug("Got demo file name: " + input_file_path + "\n")
        logging.debug("Parsing demo file\n")
        parsed_demo_data = parsing.parse_demo_file(input_file_path)
        logging.debug("Parsed demo file\n")
        logging.debug("Extracting player information\n")
        player_information = parsing.extract_player_information(parsed_demo_data)
        logging.debug("Extracted player information\n")
        logging.debug("Asking user for output file name\n")
        output_file_path = get_csv_output_file_name()
        logging.debug("Got output file name: " + output_file_path + "\n")
        logging.debug("Writing player information to output file\n")
        parsing.write_player_information_to_csv(player_information, output_file_path)
        logging.debug("Wrote player information to output file\n")
        logging.debug("Done\n")
        logging.debug("----------------------------------------------------\n")
    except Exception as error:
        logging.error(f"ERROR: {str(error)}\n")

def extract_data_console_version() -> None:
    """
    Run the main 'extract data' routine in console mode
    """

    root = tk.Tk()
    # To open file dialog in a new window on top of everything else instead of behind everything else
    root.wm_attributes('-topmost', 1)
    root.withdraw()

    print("Select the .dem file from which you would like to extract the data (see new window):")
    input_file_path = get_demo_file_name()
    if input_file_path == "":
        print("No file selected, exiting.")
        return
    print(f"Loading demo file at {input_file_path}, please wait...")
    parsed_demo_data = parsing.parse_demo_file(input_file_path)
    print("Loaded demo file.")
    print("Extracting player location information, please wait...")
    player_information = parsing.extract_player_information(parsed_demo_data)
    print("Extracted player location information.")
    print("Select to where you would like the output .csv file to save (see new window):")
    output_file_path = get_csv_output_file_name()
    print(f"Saving to {output_file_path}")
    parsing.write_player_information_to_csv(player_information, output_file_path)
    print("Wrote player location information to output file.")

    print("Extracting team area controlled information, please wait...")
    area_data = mathing.get_area_controlled_information_for_game(parsed_demo_data)
    print("Extracted team area controlled information.")
    print("Select to where you would like the output .csv file to save (see new window):")
    output_file_path = get_csv_output_file_name()
    print(f"Saving to {output_file_path}")
    parsing.write_area_controlled_information_to_csv(area_data, output_file_path)
    print("Wrote team area controlled information to output file.")

    do_save_gifs: bool = None
    while do_save_gifs is None:
        print("Would you like to save .gifs of each round visualizing player locations? (This will take some time.) (Y/N)")
        user_input = input("Enter your choice: ").upper()
        if user_input not in ["Y", "N"]:
            print("Invalid input. Please try again.")
            continue
        if user_input == "Y":
            do_save_gifs = True
        if user_input == "N":
            do_save_gifs = False
    if do_save_gifs is True:
        print("Select the directory where you would like the .gif files to be saved (see new window):")
        gif_output_directory = get_gif_output_directory()
        print(f"Saving .gifs to {gif_output_directory}")
        plotting.plot_rounds(parsed_demo_data, gif_output_directory)
        print("Saved .gifs.")
    print("Done!")
    
def console_main() -> None:
    """
    Launch CLI version of the program
    """
    print("Welcome to the CS:GO Demo File Player Data Extractor!")
    do_quit: bool = False
    while do_quit is False:
        print("Select an option:")
        print("""1. Extract data from a .dem file, creating a .csv file for player positions, area controlled,
        and .gifs for visualizing the area controlled by each team.""")
        print("Q. Quit")
        user_input = input("Enter your choice: ").upper()
        if user_input not in ["1", "Q"]:
            print("Invalid input. Please try again.")
            continue
        if user_input == "1":
            extract_data_console_version()
        if user_input == "Q":
            do_quit = True
            input("Closing. Press ENTER to continue.")
            return

def main():
    """
    """
    logging.basicConfig(filename="debug.log", encoding="utf-8", level=logging.DEBUG)

    window = tk.Tk()
    window.wm_title("CS:GO Demo File Player Data Extractor")
    # Commenting this out to see if it stops raising an issue with certain anti-virus software
    # window.wm_iconbitmap("csgo.ico")
    window.geometry("450x250")
    open_file_button = tk.Button(
        window,
        text = "Extract Data from .dem File\n(opens a file dialog)",
        bd = 10,
        bg = "grey",
        fg = "white",
        font = "Helvetica",
        height = 2,
        command = run,
        padx = 10,
        pady = 10,
        relief = "groove",
    )
    open_file_button.pack(fill=tk.BOTH, side=tk.LEFT, expand=tk.YES)
    center(window)
    window.mainloop()

if __name__ == "__main__":
    # main()
    console_main()