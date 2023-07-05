import logging
import tkinter as tk
from tkinter import Label, Menu, filedialog, ttk

import matplotlib.cm as cm
import matplotlib.pyplot as plt
import SimpleITK as sitk

from fileMenu import FileMenu
from helpMenu import HelpMenu
from ITKsegmentationframe import ITKsegmentationFrame
from ITKviewerframe import ITKviewerFrame
from topbar import Topbar
from ImagesFrameManager import imagesFrameManager
#import progressbar



logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.INFO)


#https://packaging.python.org/en/latest/guides/creating-and-discovering-plugins/
import importlib
import pkgutil

discovered_plugins = {
    name[18:]: importlib.import_module(name).main_class
    for finder, name, ispkg 
    in pkgutil.iter_modules()
    if name.startswith('itk_viewer_plugin_')
}
logging.info(discovered_plugins)

class Colors:
    """ Colors to RGB value """
    Black   = [0, 0, 0, 125]
    White   = [255, 255, 255, 125]
    Red     = [255, 0, 0, 125]
    Lime    = [0, 255, 0, 125]
    Blue    = [0, 0, 255, 125]
    Yellow  = [255, 255, 0, 125]
    Cyan    = [0, 255, 255, 125]
    Magenta = [255, 0, 255, 125]
    Silver  = [192, 192, 192, 125]
    Gray    = [128, 128, 128, 125]
    Maroon  = [128, 0, 0, 125]
    Olive   = [128, 128, 0, 125]
    Green   = [0, 128, 0, 125]
    Purple  = [128, 0, 128, 125]
    Teal    = [0, 128, 128, 125]
    Navy    = [0, 0, 128, 125]



class MainWindow(ttk.Frame):
    """ Main window class """
    plugins = {}
    
    segmentation_modes = ["None"]
    current_segmentation_mode = segmentation_modes[0]

    def __init__(self, mainframe):
        """ Initialize the main Frame """
        ttk.Frame.__init__(self, master=mainframe)
        self.load_plugins()
        self.mainframe = mainframe
        self.master.title('ITK viewer')
        self.master.geometry('800x800')  # size of the main window
        self.current_segmentation_mode = tk.StringVar(self.master)
        self.current_segmentation_mode.set(self.segmentation_modes[0])
        #TO DO: https://stackoverflow.com/a/41679642
        self.menubar = Menu(self.master)
        
        self.filemenu = FileMenu(self, self.menubar)
        self.menubar.add_cascade(label="File", menu=self.filemenu)

        self.helpmenu = HelpMenu(self, self.menubar)
        self.menubar.add_cascade(label="Help", menu=self.helpmenu)
        
        self.master.config(menu = self.menubar)

        self.label1 = Topbar(self, self.master)
        self.label1.grid(row=0, column=0, columnspan = 3, pady=5, sticky = tk.W + tk.E)

        self.label2 = tk.Label(self.master, text="Placeholder left\n\n\n\nPlaceholder left", bg="blue")
        self.label2.grid(row=1, column=0, pady=1, sticky = tk.N + tk.S)

        self.ITKviewer = imagesFrameManager(self.mainframe, image_label_layout = [[0,[1,2,3]]], bg = "yellow") # create ITK Frame
        # self.ITKviewer = ITKviewerFrame(self.mainframe, bg = "yellow") # create ITK Frame
        self.ITKviewer.grid(row=1, column=1, columnspan = 2, sticky= tk.N + tk.S + tk.E + tk.W)  # show ITK 
        
        self.ITKviewer.rowconfigure(0, weight=1)
        self.ITKviewer.columnconfigure(0, weight=1)
        self.master.rowconfigure(1, weight=1)
        self.master.columnconfigure(1, weight=1)


        self.label3 = tk.Label(self.master, text="Placeholder bottom", bg="green")
        self.label3.grid(row=2, column=0, columnspan = 3, pady=1, sticky = tk.W + tk.E)

        self.np_CT_array = None

    def new_image_input(self):
        """ Placeholder"""
        self.master.update_idletasks()
        logging.info('Importing patient data')
        DICOM_DIR = self.filemenu.get_filename()
        logging.debug(f'Importing patient data: {DICOM_DIR}')

        self.reader = sitk.ImageSeriesReader()
        
        dicom_names = self.reader.GetGDCMSeriesFileNames(DICOM_DIR)
        self.reader.SetFileNames(dicom_names)
        
        #Needed to preload meta data?????
        #self.reader.LoadPrivateTagsOn()
        logging.debug(self.reader)
        self.reader.MetaDataDictionaryArrayUpdateOn()

        self.CT_ITK_images = self.reader.Execute()
        
        if self.reader.GetMetaData(slice = 0, key ="0008|0060") != "CT":
            logging.error("Not a CT image")
        # window = self.reader.GetMetaData(slice = 0, key ="0028|1050")
        # level = self.reader.GetMetaData(slice = 0, key ="0028|1051")

        # logging.info(f'Window: {window}, level: {level}')
        # window = int(window)
        # level = int(level)

        self.np_CT_array = sitk.GetArrayFromImage(self.CT_ITK_images)
        self.ITKviewer.load_new_CT(ITK_image = self.CT_ITK_images)

    def load_plugins(self):
        """ Placeholder"""
        logging.info('Loading plugins')
        for plugin in discovered_plugins:
            self.plugins[plugin] = discovered_plugins[plugin](self)
            self.plugins[plugin].load_plugin()
        logging.info(f'Loaded plugins: {self.plugins}')

    def segmentation_mode_changed(self, *args):
        """ Placeholder"""
        logging.info(f'Segmentation mode changed to: {self.current_segmentation_mode.get()}')
        



def donothing():
    """ Place holder callback"""


if __name__ == "__main__":        
    ITKapp = tk.Tk()
    app = MainWindow(ITKapp)
    ITKapp.mainloop()

