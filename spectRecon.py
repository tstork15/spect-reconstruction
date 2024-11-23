import tkinter as tk
from tkinter import filedialog
from tkinter import ttk
import pydicom
from pytomography_functions import reconstruction
from pytomography.io.SPECT import dicom
import os

# Initialize global variable
file_path = None
ds = None
reconstructed_object = None

def select_file_and_display_data():
    """
    Open a file dialog to select a DICOM file

    Inputs: None
    Outputs: None
    """
    # Open a file dialog to select a DICOM file and get its path
    global file_path, ds
    file_path = filedialog.askopenfilename(title="Select DICOM file", filetypes=[("DICOM files", "*.dcm")])

    # Read the modality from the selected DICOM file
    ds = pydicom.read_file(file_path)
    modality = ds.Modality
    imageType = ds.ImageType

    if modality in 'NM' and 'TOMO' in imageType and 'RECON' not in imageType:
        # Clear any existing rows in the treeview
        tree.delete(*tree.get_children())

        # Get the different images
        for i in range(len(ds.EnergyWindowInformationSequence)):
            windowName = ds.EnergyWindowInformationSequence[i].EnergyWindowName
            lowerLimit = ds.EnergyWindowInformationSequence[i].EnergyWindowRangeSequence[0].EnergyWindowLowerLimit
            upperLimit = ds.EnergyWindowInformationSequence[i].EnergyWindowRangeSequence[0].EnergyWindowUpperLimit
            middleLimit = (lowerLimit + upperLimit) / 2

            tree.insert("", "end", values=(windowName, lowerLimit, upperLimit, middleLimit),
                        tags=("evenrow" if i % 2 == 0 else "oddrow"), iid=i)

    else:
        # The selected DICOM isn't a tomographic SPECT image
        tk.messagebox.showwarning("Error","Please select a unreconstructed SPECT image.")

        # Clear any existing rows in the treeview
        tree.delete(*tree.get_children())

def create_context_menu():
    """
    Create a context menu for labeling treeview items.
    """
    menu = tk.Menu(root, tearoff=0)
    menu.add_command(label="Set as Main Window", command=lambda: set_label("Main"))
    menu.add_command(label="Set as Scatter Window", command=lambda: set_label("Scatter"))
    menu.add_command(label="Clear Label", command=lambda: set_label(None))
    return menu


def set_label(label_type):
    """
    Assign a label to the selected tree item.

    Inputs:
        label_type: str, either "Main", "Scatter", or None to clear the label
    Outputs: None
    """
    selected_item = tree.selection()
    if not selected_item:
        return

    item_id = selected_item[0]
    current_label = tree.item(item_id, "values")[-1]

    if label_type == "Main":
        # Ensure only one main window
        global main_window
        if main_window:
            tree.set(main_window, "Label", "")
        main_window = item_id
        tree.set(main_window, "Label", "Main")

    elif label_type == "Scatter":
        # Allow up to two scatter windows
        global scatter_windows
        if current_label == "Scatter":
            scatter_windows.remove(item_id)
            tree.set(item_id, "Label", "")
        elif len(scatter_windows) < 2:
            scatter_windows.append(item_id)
            tree.set(item_id, "Label", "Scatter")

    elif label_type is None:
        # Clear label
        if current_label == "Main":
            main_window = None
        elif current_label == "Scatter":
            scatter_windows.remove(item_id)
        tree.set(item_id, "Label", "")


def on_right_click(event):
    """
    Handle right-clicks on the treeview to show the context menu.
    """
    item = tree.identify_row(event.y)
    if item:
        tree.selection_set(item)
        context_menu.post(event.x_root, event.y_root)

def reconstruct():
    """
    Handle the Reconstruct button click.
    If no main window is assigned, inform the user.
    If the main window is assigned, reconstruct.
    """
    global reconstructed_object
    if main_window is None:
        # Inform the user that they need to assign a main window
        tk.messagebox.showwarning("No Main Window", "Please right-click to assign a 'Main Window' before reconstructing.")
    else:
        # Get the values for iterations and subsets
        iterations = int(iterations_input.get())
        subsets = int(subsets_input.get())

        # Ensure the parameters are 1 or greater
        if iterations > 0 and subsets > 0:
            # Check if two scatter windows were defined
            if len(scatter_windows) == 2:
                # Determine which energy window is the upper scatter and lower scatter
                if ds.EnergyWindowInformationSequence[int(scatter_windows[0])].EnergyWindowRangeSequence[0].EnergyWindowLowerLimit < ds.EnergyWindowInformationSequence[int(scatter_windows[1])].EnergyWindowRangeSequence[0].EnergyWindowLowerLimit:
                    lower_scatter = scatter_windows[0]
                    upper_scatter = scatter_windows[1]
                else:
                    lower_scatter = scatter_windows[1]
                    upper_scatter = scatter_windows[0]

                # Reconstruct with both scatter windows
                reconstructed_object = reconstruction(file_path, int(main_window), lower_scatter_index=int(lower_scatter),
                                                      upper_scatter_index=int(upper_scatter), iterations=iterations, subsets=subsets)
            elif len(scatter_windows) == 1:
                # Determine if the scatter window is an upper or lower
                if ds.EnergyWindowInformationSequence[int(scatter_windows[0])].EnergyWindowRangeSequence[0].EnergyWindowLowerLimit < ds.EnergyWindowInformationSequence[int(main_window)].EnergyWindowRangeSequence[0].EnergyWindowLowerLimit:
                    lower_scatter = scatter_windows[0]

                    # Reconstruct with only a lower scatter window
                    reconstructed_object = reconstruction(file_path, int(main_window), lower_scatter_index=int(lower_scatter),
                                                          iterations=iterations, subsets=subsets)
                else:
                    upper_scatter = scatter_windows[0]

                    # Reconstruct with only an upper scatter window
                    reconstructed_object = reconstruction(file_path, int(main_window), upper_scatter_index=int(upper_scatter),
                                                          iterations=iterations, subsets=subsets)
            else:
                # Reconstruct without any scatter windows
                reconstructed_object = reconstruction(file_path, int(main_window), iterations=iterations, subsets=subsets)
        else:
            # Inform the user that they need to enter positive numbers
            tk.messagebox.showwarning("Error",
                                      "Please enter positive numbers for the iterations and subsets.")

def save():
    # Ensure a reconstruction has been created
    if reconstructed_object is not None:
        # Build the folder to save the reconstruction to
        save_path = filedialog.askdirectory()
        save_folder = save_name_entry.get()
        save_path = os.path.join(save_path, save_folder)
        try:
            # Try saving
            dicom.save_dcm(
                save_path=save_path,
                object=reconstructed_object,
                file_NM=file_path,
                recon_name=save_folder)
        except:
            tk.messagebox.showwarning("Error", "Please create a new folder.")
            #TODO: hook up iterations/subsets
    else:
        tk.messagebox.showwarning("Error", "Please create a reconstruction.")

if __name__ == "__main__":
    root = tk.Tk()
    root.title("SPECT Reconstruction")

    frame = tk.Frame(root)
    frame.pack(padx=10, pady=10)

    select_file_button = tk.Button(frame, text="Select DICOM File", command=select_file_and_display_data)
    select_file_button.pack(side=tk.LEFT, padx=5, pady=5)

    tree_frame = tk.Frame(root)
    tree_frame.pack(fill=tk.X, padx=10, pady=10)

    columns = ("Energy Window Name", "Lower Limit (keV)", "Upper Limit (keV)", "Center (keV)", "Label")
    tree = ttk.Treeview(tree_frame, columns=columns, show="headings")
    tree.pack(fill=tk.BOTH, expand=True)

    # param frame for iterations, subsets, and reconstruct button
    bottom_frame = tk.Frame(root)
    bottom_frame.pack(padx=10, pady=10, fill=tk.X)

    # Subframe for iterations, subsets, and reconstruct button
    param_frame = tk.Frame(bottom_frame)
    param_frame.pack(fill=tk.X)

    # Label and input for iterations
    iterations_label = tk.Label(param_frame, text="Iterations:")
    iterations_label.pack(side=tk.LEFT, padx=5, pady=5)
    iterations_input = tk.Spinbox(param_frame, from_=1, to=100, width=5)
    iterations_input.delete(0, tk.END)
    iterations_input.insert(0, "4")
    iterations_input.pack(side=tk.LEFT, padx=5, pady=5)

    # Label and input for subsets
    subsets_label = tk.Label(param_frame, text="Subsets:")
    subsets_label.pack(side=tk.LEFT, padx=5, pady=5)
    subsets_input = tk.Spinbox(param_frame, from_=1, to=100, width=5)
    subsets_input.delete(0, tk.END)
    subsets_input.insert(0, "8")
    subsets_input.pack(side=tk.LEFT, padx=5, pady=5)

    # Reconstruct button in the param frame
    reconstruct_button = tk.Button(param_frame, text="Reconstruct", command=reconstruct)
    reconstruct_button.pack(side=tk.LEFT, padx=5, pady=5)

    # Subframe for save button and text input
    save_frame = tk.Frame(bottom_frame)
    save_frame.pack(fill=tk.X, pady=(10, 0))

    # Text input for folder name
    save_name_label = tk.Label(save_frame, text="Folder Name:")
    save_name_label.pack(side=tk.LEFT, padx=5)
    save_name_entry = tk.Entry(save_frame, width=20)
    save_name_entry.pack(side=tk.LEFT, padx=5)

    # Save button in the save frame
    save_button = tk.Button(save_frame, text="Save Reconstruction", command=save)
    save_button.pack(side=tk.LEFT, padx=5, pady=5)

    root.geometry("800x600")

    for col in columns:
        tree.heading(col, text=col)

    tree.grid(row=0, column=0, sticky="nsew")

    tree_frame.grid_rowconfigure(0, weight=1)
    tree_frame.grid_columnconfigure(0, weight=1)

    # Adjust column widths to fit within the available space
    def adjust_columns(event=None):
        total_width = tree.winfo_width()
        num_columns = len(columns)
        column_width = total_width // num_columns  # Distribute space equally
        for col in columns:
            tree.column(col, width=column_width, anchor="center")


    # Bind the window resize event to adjust column widths
    tree_frame.bind("<Configure>", adjust_columns)

    main_window = None
    scatter_windows = []

    context_menu = create_context_menu()
    tree.bind("<Button-3>", on_right_click)  # Bind right-click to the treeview

    tree.tag_configure("evenrow", background="lightgrey")  # Configure the background color for even rows
    tree.tag_configure("oddrow", background="white")  # Configure the background color for odd rows

    root.mainloop()