import tkinter as tk  
from tkinter import filedialog
import logging

def donothing():
    """ Place holder callback"""

class SegemntationMenu(tk.Menu):
    """ """
    def __init__(self, parent, menubar):
        """ Initiliaze menu bar """
        tk.Menu.__init__(self, menubar, tearoff=0)
        self.parent = parent
        self.initialize()
        self.segmentation_folder = None
    
    def initialize(self):
        """ Initiliaze menu bar """
        self.add_command(label="Open", command = self.segmentation_opener)
        self.add_command(label="Save", command=self.segmentation_saver)
        self.add_command(label="Save as", command=self.segmentation_save_as)
        self.add_separator()
        self.add_command(label="About", command=donothing)
    
    def segmentation_opener(self):
        """ Open file callback """
        #https://docs.python.org/3/library/dialog.html#tkinter.filedialog.askdirectory
        self.ask_segmentation_folder()
        self.parent.load_segmentations()

    def ask_segmentation_folder(self):
        """ placeholder """
        self.segmentation_folder = filedialog.askdirectory(mustexist = True)
        logging.debug(self.segmentation_folder)

    def segmentation_save_as(self):
        """ placeholder """
        self.ask_segmentation_folder()
        self.parent.save_segmentations()

    def segmentation_saver(self):
        """ placeholder """
        if self.segmentation_folder is None:
            self.ask_segmentation_folder()
        
        self.parent.save_segmentations()