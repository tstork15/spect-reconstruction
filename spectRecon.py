import tkinter as tk
from tkinter import filedialog
from tkinter import ttk
import pydicom
import numpy as np

def select_file_and_display_data():
    """
    Open a file dialog to select a DICOM file

    Inputs: None
    Outputs: None
    """
    # Open a file dialog to select a DICOM file and get its path
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
                        tags=("evenrow" if i % 2 == 0 else "oddrow"))

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
    if main_window is None:
        # Inform the user that they need to assign a main window
        tk.messagebox.showwarning("No Main Window", "Please right-click to assign a 'Main Window' before reconstructing.")
    else:
        # Placeholder for reconstruction logic
        print("Reconstructing with the selected main window...")


if __name__ == "__main__":
    root = tk.Tk()
    root.title("SPECT Reconstruction")
    frame = tk.Frame(root)
    frame.pack(padx=10, pady=10)

    select_file_button = tk.Button(frame, text="Select DICOM File", command=select_file_and_display_data)
    select_file_button.pack(side=tk.LEFT, padx=5, pady=5)

    reconstruct_button = tk.Button(frame, text="Reconstruct", command=reconstruct)
    reconstruct_button.pack(side=tk.LEFT, padx=5, pady=5)

    root.geometry("800x600")

    tree_frame = tk.Frame(root)
    tree_frame.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)

    columns = ("Energy Window Name", "Lower Limit (keV)", "Upper Limit (keV)", "Center (keV)", "Label")
    tree = ttk.Treeview(tree_frame, columns=columns, show="headings")

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

    root.mainloop()


