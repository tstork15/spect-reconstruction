import tkinter as tk
from tkinter import filedialog
from tkinter import ttk
import tkinter.font as tkFont
import os
from PIL import Image, ImageTk, ImageOps
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
        print("Please select a unreconstructed SPECT image.")

        # Clear any existing rows in the treeview
        tree.delete(*tree.get_children())

if __name__ == "__main__":
    root = tk.Tk()  # Create the main window
    root.title("SPECT Reconstruction")  # Set the window title

    frame = tk.Frame(root)  # Create a frame to hold the buttons and dropdown
    frame.pack(padx=10, pady=10)  # Add padding around the frame

    select_file_button = tk.Button(frame, text="Select DICOM File", command=select_file_and_display_data)   # Button to select a DICOM file
    select_file_button.pack(side=tk.LEFT, padx=5, pady=5)  # Pack the button with padding

    # Set default window size
    root.geometry("800x600")  # Set the default size of the main window

    # Treeview setup
    tree_frame = tk.Frame(root)
    tree_frame.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)

    columns = ("Energy Window Name", "Lower Limit (keV)", "Upper Limit (keV)", "Center (keV)")
    tree = ttk.Treeview(tree_frame, columns=columns, show="headings")

    for col in columns:
        tree.heading(col, text=col)

    tree.grid(row=0, column=0, sticky="nsew")

    # Scrollbar
    scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=tree.yview)
    tree.configure(yscroll=scrollbar.set)
    scrollbar.grid(row=0, column=1, sticky="ns")

    # Configure grid weights
    tree_frame.grid_rowconfigure(0, weight=1)
    tree_frame.grid_columnconfigure(0, weight=1)

    # Alternating row colors
    tree.tag_configure("evenrow", background="lightgrey")
    tree.tag_configure("oddrow", background="white")

    root.mainloop()  # Start the Tkinter main loop
