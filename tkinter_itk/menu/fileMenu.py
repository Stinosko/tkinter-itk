import tkinter as tk  
from tkinter import filedialog
import logging

class FileMenu(tk.Menu):
    """ Nested class for file menu bar functionality """
    def __init__(self, parent, menubar):
        """ Initiliaze menu bar """
        tk.Menu.__init__(self, menubar, tearoff=0)
        self.parent = parent
        self.filename = None
        self.initialize()

    def initialize(self):
        """ Initiliaze menu bar """
        self.add_command(label="Open", command = self.file_opener)
        # self.add_command(label="Save", command=self.get_filename)
        self.add_separator()
        self.add_command(label="Exit", command=self.master.quit)

    def file_opener(self):
        """ Open file callback """
        #https://docs.python.org/3/library/dialog.html#tkinter.filedialog.askdirectory
        self.filename = filedialog.askdirectory(mustexist = True)
        logging.debug(self.filename)
        self.parent.new_image_input()

    def get_filename(self):
        """ Return last opened filename """
        return self.filename