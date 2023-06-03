import SimpleITK as sitk
import numpy as np
from PIL import Image, ImageTk
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import logging


#Create Menubar in Python GUI Application  
import tkinter as tk  
from tkinter import ttk, Label, Menu, filedialog
import random

from skimage.feature import hessian_matrix, hessian_matrix_eigvals
from skimage.draw import line

import math, os
import warnings
#import progressbar

import multiprocessing
import shutil
import operator
import time

logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.DEBUG)




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

def zoom_at(img, x = 0, y =0, zoom = 1, interpolate = Image.LANCZOS):
    w, h = img.size
    zoom2 = zoom * 2
    img = img.crop((x - w / zoom2, y - h / zoom2, 
                    x + w / zoom2, y + h / zoom2))
    return img.resize((w, h), interpolate)


class ITKviewerFrame(tk.Frame):
    """ ITK viewer Frame """
    def __init__(self, mainframe):
        """ Initialize the ITK viewer Frame """
        tk.Frame.__init__(self, master = mainframe)
        self.mainframe = mainframe

        self.initialize()

        self.image = ImageTk.PhotoImage(self.get_image_from_HU_array())  # create image object

        self.image_Frame = tk.Frame(self.master, width=150)
        self.image_label = Label(self.image_Frame, image=self.image)
        self.image_label.grid(row=0, column=0, columnspan = 2)
        self.mouse_location_HU = tk.Label(self.image_Frame, text=f"Window: {self.window}, Level: {self.level}")
        self.mouse_location_HU.grid(row=1, column=0, sticky=tk.E, pady=1) 
        
        self.image_Frame.grid(row=1, column=2, columnspan = 3)

    def initialize(self):
        """ placeholder """
        self.zoom_delta = 1 
        self.slice_index = 1
        self.np_HU_array = np.empty((512,512,512))
        self.window = 1400
        self.level = 300

        self.center_X = self.np_HU_array.shape[1] /2
        self.center_Y = self.np_HU_array.shape[2] /2

        self.interpolate = Image.NEAREST

        self.mainframe.bind('<MouseWheel>', self.__scroll)  # zoom for Windows and MacOS, but not Linux
        self.mainframe.bind('<Button-5>',   self.__scroll)  # zoom for Linux, wheel scroll down
        self.mainframe.bind('<Button-4>',   self.__scroll)  # zoom for Linux, wheel scroll up
        self.mainframe.bind('<Up>', lambda event: self.next_slice())
        self.mainframe.bind('<Down>', lambda event: self.previous_slice())
        self.mainframe.bind('<Right>', lambda event: self.zoom_in())
        self.mainframe.bind('<Left>', lambda event: self.zoom_out())
        self.mainframe.bind('<Control-B1-Motion>', self.pan_image)
        self.mainframe.bind('<Shift-B1-Motion>', self.change_window_level)
        self.mainframe.bind('<ButtonPress-1>', self.start_drag_event_image) #stop_pan_image
        self.mainframe.bind('<ButtonRelease-1>', self.stop_drag_event_image)

    def get_empty_image(self):
        """ Return empty image """
        return Image.new("RGB", (512, 512), (0, 0, 0))

    def get_image_from_HU_array(self):
        minimum_hu = self.level - (self.window/2)
        maximum_hu  = self.level + (self.window/2)

        np_HU_2D_array = np.copy(self.np_HU_array[self.slice_index,:,:])
        np_HU_2D_array[np_HU_2D_array < minimum_hu] = minimum_hu
        np_HU_2D_array[np_HU_2D_array > maximum_hu] = maximum_hu

        try:
            np_gray_array = np.divide(np_HU_2D_array - np_HU_2D_array.min(), 
                                (np_HU_2D_array.max() - np_HU_2D_array.min())
                                )*255
        except Exception as e:
            logging.error(e)
        np_gray_array = np_gray_array.astype(np.uint8)

        img_arr = Image.fromarray(np_gray_array, "L").convert('RGBA')
        
        
        logging.debug("zooming in")
        img_arr = zoom_at(img_arr, x = self.center_X, y = self.center_Y, zoom= self.zoom_delta, interpolate= self.interpolate)


        return img_arr

    def update_image(self):
        """placeholder"""
        self.image = ImageTk.PhotoImage(self.get_image_from_HU_array())
        self.image_label.configure(image=self.image)

    def load_new_CT(self, np_HU_array: np.ndarray):
        """placeholder"""
        self.np_HU_array = np_HU_array
        
        self.center_X = self.np_HU_array.shape[1] /2
        self.center_Y = self.np_HU_array.shape[2] /2
        
        self.update_image()

    def __scroll(self, event):
        logging.debug("Scrolling")
        if event.delta == -120:  # scroll down, smaller
            self.previous_slice()
        if event.delta == 120:  # scroll up, bigger
            self.next_slice()
       
        

    def next_slice(self):
        logging.debug("Next slice")
        self.slice_index += 1
        CT_image_cache = None
        if self.slice_index >= self.np_HU_array.shape[0]:
            self.slice_index = self.np_HU_array.shape[0] - 1
        self.update_image()
        
    def previous_slice(self):
        logging.debug("Previous slice")
        self.slice_index -= 1
        CT_image_cache = None
        if self.slice_index < 0:
            self.slice_index = 0
        self.update_image()

    def zoom(self, event):
        ""
        logging.debug("zooming")
        if event.delta == -120:  # scroll down, smaller
            self.zoom_out()
        if event.delta == 120:  # scroll up, bigger
            self.zoom_in()
        

    def zoom_in(self):
        logging.debug("Zoom In")
        self.zoom_delta += 0.1
        self.update_image()

    def zoom_out(self):
        logging.debug("Zoom out")
        self.zoom_delta -= 0.1
        self.update_image()
    
    def pan_image(self, event):
        " "
        self.mainframe.update_idletasks()
        if (self.start_click_location_X == event.x or self.start_click_location_X == None) and (self.start_click_location_Y == event.y or self.start_click_location_Y == None):
            logging.error("pan invalid")
            return
        logging.debug("doing pan")
        self.center_X += (self.start_click_location_X - event.x) / self.zoom_delta
        self.center_Y += (self.start_click_location_Y - event.y) / self.zoom_delta

        self.start_click_location_X = event.x
        self.start_click_location_Y = event.y

        self.update_image()

    def start_drag_event_image(self, event):
        logging.debug("start pan")
        self.start_click_location_X = event.x
        self.start_click_location_Y = event.y

    def stop_drag_event_image(self, event):
        logging.debug("stop pan")
        self.start_click_location_X = None
        self.start_click_location_Y = None
        
    def change_window_level(self, event):
        self.mainframe.update_idletasks()
        if (self.start_click_location_X == event.x or self.start_click_location_X == None) and (self.start_click_location_Y == event.y or self.start_click_location_Y == None):
            logging.error(" windowing invalid")
            return
        logging.debug("windowing pan")
        self.window += self.start_click_location_X - event.x
        self.level += self.start_click_location_Y - event.y

        self.start_click_location_X = event.x
        self.start_click_location_Y = event.y

        self.mouse_location_HU.config(text=f"Window: {self.window}, Level: {self.level}")

        self.update_image()




class MainWindow(ttk.Frame):
    """ Main window class """
    def __init__(self, mainframe):
        """ Initialize the main Frame """
        ttk.Frame.__init__(self, master=mainframe)

        self.master.title('ITK viewer')
        self.master.geometry('800x600')  # size of the main window

        #TO DO: https://stackoverflow.com/a/41679642
        self.menubar = Menu(self.master)
        
        self.filemenu = FileMenu(self, self.menubar)
        self.menubar.add_cascade(label="File", menu=self.filemenu)

        self.helpmenu = HelpMenu(self, self.menubar)
        self.menubar.add_cascade(label="Help", menu=self.helpmenu)
        
        self.master.config(menu = self.menubar)

        self.label1 = tk.Label(self.master, text="Placeholder top")
        self.label1.grid(row=0, column=0, columnspan = 3, pady=1)

        self.label2 = tk.Label(self.master, text="Placeholder left\n\n\n\nPlaceholder left")
        self.label2.grid(row=1, column=0, pady=1)

        self.ITKviewer = ITKviewerFrame(self.master) # create ITK Frame
        self.ITKviewer.grid(row=1, column=1, columnspan = 2)  # show ITK 

        self.label3 = tk.Label(self.master, text="Placeholder bottom")
        self.label3.grid(row=2, column=0, columnspan = 3, pady=1)

        self.np_CT_array = None

    def new_image_input(self):
        """ Placeholder"""
        logging.info('Importing patient data')
        DICOM_DIR = self.filemenu.get_filename()
        logging.debug(f'Importing patient data: {DICOM_DIR}')

        self.reader = sitk.ImageSeriesReader()
        
        dicom_names = self.reader.GetGDCMSeriesFileNames(DICOM_DIR)
        self.reader.SetFileNames(dicom_names)
        
        #Needed to preload meta data?????
        self.reader.LoadPrivateTagsOn()
        
        logging.debug(self.reader)
        
        self.reader.MetaDataDictionaryArrayUpdateOn()
        


        self.CT_ITK_images = self.reader.Execute()

        #self.CT_ITK_images.ReadImageInformation()
        for k in self.reader.GetMetaDataKeys(slice = 1):
            v = self.reader.GetMetaData(slice = 1, key = k)
            print(f'({k}) = = "{v}"')    
    
        self.np_CT_array = sitk.GetArrayFromImage(self.CT_ITK_images)
        self.ITKviewer.load_new_CT(self.np_CT_array)
           



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
        self.add_command(label="Save", command=self.get_filename)
        self.add_separator()
        self.add_command(label="Exit", command=self.master.quit)

    def file_opener(self):
        """ Open file callback """
        #https://docs.python.org/3/library/dialog.html#tkinter.filedialog.askdirectory
        # Not sure mustexist = True works or it is even needed
        self.filename = filedialog.askdirectory(mustexist = True)
        logging.debug(self.filename)
        self.parent.new_image_input()

    def get_filename(self):
        """ Return last opened filename """
        return self.filename


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
        
        if self.parent.np_CT_array is None:
            logging.warning("no image loaded")
            return
        top= tk.Toplevel(self.parent)
        top.geometry("750x250")
        top.title("Child Window")
        
        txt = "DICOM info of {}".format(self.parent.filemenu.get_filename())
        for k in self.parent.CT_ITK_images.GetMetaDataKeys():
            v = self.parent.CT_ITK_images.GetMetaData(k)
            txt += f"({k}) = = \"{v}\" \n"
        print(txt)
        Label(top, text= txt).place(x=10,y=10)
        
        

def donothing():
    """ Place holder callback"""


if __name__ == "__main__":    
    logging.debug('This message should appear on the console')
    logging.info('So should this')
    logging.warning('And this, too')
    
    ITKapp = tk.Tk()
    app = MainWindow(ITKapp)
    ITKapp.mainloop()

