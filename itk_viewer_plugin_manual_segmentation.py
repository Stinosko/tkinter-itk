import tkinter as tk  
from tkinter import ttk, Label, Menu, filedialog
import logging
import numpy as np
from Utils import Spinbox

class manual_segmentation:
    name_short = "manual"
    name_long = "manual segmentation"
    def __init__(self, parent, **kwargs):
        self.parent = parent
        self.layer_height = 1
    def load_plugin(self):
        self.parent.segmentation_modes.append(self.__class__.__name__)

    def __str__(self) -> str:
        return "ITK viewer plugin manual segmentation"
    def get_segmentation_options(self, parent):
        self.__previous_state = 0
        self.parent.master.bind('ButtonPress-1>', self.test, add="+")
        self.frame = tk.Frame(parent)
        self.frame.grid(row=0, column=1, sticky=tk.E + tk.W, pady=1)

        self.layer_frame = tk.Frame(self.frame)
        self.layer_label = tk.Label(self.layer_frame, text="Layer")
        self.layer_label.grid(row=0, column=0, sticky=tk.E + tk.W, pady=1)
        self.layer_entry = Spinbox(self.layer_frame, from_=1, to=self.parent.ITKviewer.max_layers, width=1, command=self.update_layer)
        self.layer_entry.grid(row=1, column=0, sticky=tk.E + tk.W, pady=1)
        self.layer_entry.bind('<Return>', lambda event: self.update_layer())
        self.layer_frame.grid(row=0, column=0, sticky=tk.E + tk.W, pady=1)

        self.button = tk.Button(self.frame, text="Clear segmentation", command=self.clear_segmentation)
        self.button.grid(row=0, column=1, sticky=tk.E + tk.W, pady=1)
        self.parent.bind_all('<ButtonPress-1>', self.button1_press_event_image)
        self.parent.bind_all('<ButtonPress-3>', self.button3_press_event_image)

        return self.frame
    
    def test(self, event):
        logging.warn("test")

    def clear_segmentation(self):
        self.parent.ITKviewer.ITK_seg_array[self.parent.ITKviewer.slice_index,: , :, :] = np.zeros(self.parent.ITKviewer.ITK_seg_array[self.parent.ITKviewer.slice_index,: , :, :].shape, dtype=bool)
        self.update_segmentation()

    def update_layer(self):
        self.layer_height = int(self.layer_entry.get())
        logging.info("update layer to %s", self.layer_height)
        self.parent.focus_set()
        

    def mouse_in_itksegmentationframe(self, event):
        #get monitor cooridnates of mouse
        x_monitor = self.parent.mainframe.winfo_pointerx()
        y_monitor = self.parent.mainframe.winfo_pointery()
        #winfo_containing requires coordinates of the the monitor screen not relative to the main window
        if "itksegmentationframe" in self.parent.mainframe.winfo_containing(x_monitor,y_monitor).winfo_parent():
            return True
        else:
            return False

    def ctrl_is_pressed(self, event):
        if event.state - self.__previous_state == 4:  # means that the Control key is pressed
            logging.debug("ctrl_is_pressed")
            return True
        else:
            return False

    def shift_is_pressed(self, event):
        if event.state - self.__previous_state == 1:
            logging.debug("shift_is_pressed")
            return True
        else:
            return False

    def ctrl_shift_is_pressed(self, event):
        if event.state - self.__previous_state == 5:
            logging.debug("ctrl_shift_is_pressed")
            return True
        else:
            return False

    def button1_press_event_image(self, event):
        logging.info("button1_press_event_image in manual segmentation")
        #get monitor cooridnates of mouse
        if self.mouse_in_itksegmentationframe(event) == False or self.ctrl_is_pressed(event) or self.shift_is_pressed(event) or self.ctrl_shift_is_pressed(event):
            logging.debug("mouse not in itksegmentationframe")
            return
        logging.debug(event.state - self.__previous_state)
        self.__previous_state = event.state  # remember the last keystroke state

        ITK_seg_array = self.parent.ITKviewer.ITK_seg_array
        y , x = self.parent.ITKviewer.get_mouse_location_dicom(event)
        ITK_seg_array[self.parent.ITKviewer.slice_index, int(x), int(y), self.layer_height] = True
        self.update_segmentation()

    def button3_press_event_image(self, event):
        logging.info("button3_press_event_image in manual segmentation")
        #get monitor cooridnates of mouse
        if self.mouse_in_itksegmentationframe(event) == False or self.ctrl_is_pressed(event) or self.shift_is_pressed(event) or self.ctrl_shift_is_pressed(event):
            logging.debug("mouse not in itksegmentationframe")
            return
        logging.debug(event.state - self.__previous_state)
        self.__previous_state = event.state

        ITK_seg_array = self.parent.ITKviewer.ITK_seg_array
        y , x = self.parent.ITKviewer.get_mouse_location_dicom(event)
        ITK_seg_array[self.parent.ITKviewer.slice_index, int(x), int(y), self.layer_height] = False
        self.update_segmentation()

    def update_segmentation(self):
        self.parent.ITKviewer.update_image()
    

main_class=manual_segmentation