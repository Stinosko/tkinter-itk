import tkinter as tk  
from tkinter import ttk, Label, Menu, filedialog
import logging


class Topbar(tk.Frame):
    """ Topbar Frame """
    def __init__(self, parent, mainframe, **kwargs):
        """ Initialize Frame """
        super().__init__(mainframe, **kwargs)
        self.parent = parent
        
        self.frame = tk.Frame(self)
        self.options = tk.OptionMenu(self.frame, self.parent.current_segmentation_mode, *self.parent.segmentation_modes, command = self.update_segmentation_options)
        self.options.grid(row=0, column=0, sticky=tk.E , pady=1)
        self.segmentation_option_frame = tk.Frame(self.frame)
        self.segmentation_option_frame.grid(row=0, column=1, sticky=tk.E + tk.W, pady=1)

        self.frame.grid(row=0, column=0, columnspan = 3, pady=5, sticky = tk.W + tk.E)
    
    def update_segmentation_options(self, new_mode):
        self.parent.segmentation_mode_changed()
        self.segmentation_option_frame.destroy()
        if new_mode == "None":
            self.segmentation_option_frame = tk.Frame(self.frame)
        else:    
            self.segmentation_option_frame = self.parent.plugins[new_mode].get_segmentation_options(self.frame)
        self.segmentation_option_frame.grid(row=0, column=1, sticky=tk.E + tk.W, pady=1)
