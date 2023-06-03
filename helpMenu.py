import tkinter as tk  
from tkinter import ttk, Label, Menu, filedialog
import logging

def donothing():
    """ Place holder callback"""

class HelpMenu(tk.Menu):
    """ Nested class for help menu bar functionality """
    def __init__(self, parent, menubar):
        """ Initiliaze menu bar """
        tk.Menu.__init__(self, menubar, tearoff=0)
        self.parent = parent
        self.initialize()

    def initialize(self):
        """ Initiliaze menu bar """
        self.add_command(label="DICOM info", command = self.display_DICOM_info)
        self.add_command(label="About", command=donothing)
        
    def display_DICOM_info(self):
        print("DICOM info")
        if self.parent.np_CT_array is None:
            logging.warning("no image loaded")
            return
        
        self.top = tk.Toplevel(self.parent)   
        # set minimum window size value
        self.top.minsize(644, 400)
        # set maximum window size value
        self.top.maxsize(644, 400) 
        self.help_label = tk.Label(self.top, text="DICOM info", width=644, height=400)
        self.help_label.grid()

        text= tk.Text(self.help_label)
        scrollbar = tk.Scrollbar(self.help_label,command=text.yview)
        text.config(yscrollcommand=scrollbar.set)
        scrollbar.grid(row=0,column=0,sticky=tk.NSEW)
        text.grid(row=0,column=1)

        txt = "DICOM info of {}".format(self.parent.filemenu.get_filename())
        for k in self.parent.reader.GetMetaDataKeys(slice = 1):
            v = self.parent.reader.GetMetaData(slice = 1, key = k)
            txt += f"({k}) = \"{v}\" \n"
        

        text.insert(tk.END, txt)