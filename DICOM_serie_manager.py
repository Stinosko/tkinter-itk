import tkinter as tk  
from tkinter import ttk, Label, Menu, filedialog
import logging
import numpy as np
from PIL import Image, ImageTk
import math
from Utils import timer_func, PatchedFrame
import SimpleITK as sitk
from ITKviewerframe import ITKviewerFrame
import os
from DICOM_serie_instance import DICOM_serie_instance

def GetGDCMSeriesIDs_recursive(DICOM_DIR, reader):
    """placeholder"""
    result = tuple()
    result = reader.GetGDCMSeriesIDs(DICOM_DIR)
    for directory in [ f.path for f in os.scandir(DICOM_DIR) if f.is_dir() ]:
        temp = GetGDCMSeriesIDs_recursive(directory, reader)
        if len(temp) > 0:
            result = result + temp
    return result



# Creating class AutoScrollbar
# https://www.geeksforgeeks.org/autohiding-scrollbars-using-python-tkinter/
class AutoScrollbar(tk.Scrollbar):
       
    # Defining set method with all 
    # its parameter
    def set(self, low, high):
           
        if float(low) <= 0.0 and float(high) >= 1.0:
               
            # Using grid_remove
            self.tk.call("grid", "remove", self)
        else:
            self.grid()
        tk.Scrollbar.set(self, low, high)
       
    # Defining pack method
    def pack(self, **kw):
           
        # If pack is used it throws an error
        raise (tk.TclError,"pack cannot be used with this widget")
       
    # Defining place method
    def place(self, **kw):
           
        # If place is used it throws an error
        raise (tk.TclError, "place cannot be used  with this widget")


class DICOM_serie_manager(PatchedFrame):
    """placeholder"""
    def __init__(self, mainframe, **kwargs):
        PatchedFrame.__init__(self, mainframe, **kwargs)
        self.mainframe = mainframe
        self.config(width=200)
        self.grid(row=2, column=0, pady=(5, 0), sticky='nw')
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.grid_propagate(False)

        self.DICOM_DIR = None 

        self.reader = sitk.ImageSeriesReader()
        self.reader.MetaDataDictionaryArrayUpdateOn()
        self.reader.LoadPrivateTagsOn()
        
        self.series_file_names = {}
        self.DICOM_DIR = os.path.join(os.getcwd(), "test-data")

        # Add a canvas in that frame
        self.canvas = tk.Canvas(self, bg="yellow")
        self.canvas.grid(row=0, column=0, sticky="news")
        
        # https://stackoverflow.com/questions/43731784/tkinter-canvas-scrollbar-with-grid
        # Link a scrollbar to the canvas
        self.vsb = AutoScrollbar(self, orient="vertical", command=self.canvas.yview)
        self.vsb.grid(row=0, column=1, sticky='ns')
        self.hsb = AutoScrollbar(self, orient="horizontal", command=self.canvas.xview)
        self.hsb.grid(row=1, column=0, sticky='ew')
        self.canvas.configure(yscrollcommand=self.vsb.set, xscrollcommand=self.hsb.set)

        # Set the canvas frame size
        column_width = 150
        row_height = 150
        self.config(width=column_width + self.vsb.winfo_width(),
                            height=row_height +  self.hsb.winfo_height())

        # Set the canvas scrolling region
        self.canvas.config(scrollregion=self.canvas.bbox("all"))

        # Create a frame to contain the buttons
        self.frame_buttons = tk.Frame(self.canvas, bg="blue")
        self.canvas.create_window((0, 0), window=self.frame_buttons, anchor='nw')
        
        self.DICOM_serie_instances = {}
        
        self.load_DICOM_serie(DICOM_DIR = self.DICOM_DIR)
        self.set_preview_frames()

    def load_DICOM_serie(self, DICOM_DIR = None, image_name = None):
        if DICOM_DIR is None:
            logging.warning("DICOM_DIR is None")
            return
        self.DICOM_DIR = DICOM_DIR
        series_file_names = {}
        series_IDs = GetGDCMSeriesIDs_recursive(DICOM_DIR, self.reader)
        # Check that we have at least one series
        if len(series_IDs) > 0 and image_name is None:
            for serie_ID in series_IDs:
                dicom_names = sitk.ImageSeriesReader_GetGDCMSeriesFileNames(DICOM_DIR, serie_ID, recursive =True)
                reader = sitk.ImageSeriesReader()
                reader.SetFileNames(dicom_names)
                reader.LoadPrivateTagsOn()
                reader.MetaDataDictionaryArrayUpdateOn()
                series_file_names[serie_ID] = reader
        elif image_name is not None:
            logging.warning("Untested code!")
            reader = sitk.ImageSeriesReader()
            reader.SetFileNames([image_name])
            reader.LoadPrivateTagsOn()
            reader.MetaDataDictionaryArrayUpdateOn()
            series_file_names[image_name] = reader
        else:
            logging.warning("Data directory does not contain any DICOM series.")
            return
        
        self.series_file_names = series_file_names

    def load_image_serie(self, image, image_name, add = False):
        if image is None:
            logging.warning("Image is None")
            return
        temp_folder = os.path.join(os.getcwd(), ".temp")
        if not add:
            self.DICOM_DIR = temp_folder
        writer = sitk.ImageFileWriter()
        
        writer.KeepOriginalImageUIDOn()
        writer.SetImageIO("NiftiImageIO")
        writer.SetFileName(os.path.join(self.DICOM_DIR, image_name + ".nii.gz"))
        writer.Execute(image)

        if not add: 
            self.series_file_names = {}
        reader = sitk.ImageSeriesReader()
        reader.SetImageIO("NiftiImageIO")
        reader.SetFileNames([os.path.join(self.DICOM_DIR, image_name)])
        reader.LoadPrivateTagsOn()
        reader.MetaDataDictionaryArrayUpdateOn()
        self.series_file_names[image_name] = reader
        return image_name

    def get_serie_reader(self, serie_ID):
        return self.series_file_names[serie_ID]

    def get_serie_IDs(self):
        return self.series_file_names.keys()

    def set_preview_frames(self):
        # Add 9-by-5 buttons to the frame
        
        self.DICOM_serie_instances = {}
        for i, serie_ID in enumerate(self.get_serie_IDs()):
            self.DICOM_serie_instances[serie_ID] = DICOM_serie_instance(self.frame_buttons, self.DICOM_DIR, serie_ID, self.get_serie_reader(serie_ID))
            self.DICOM_serie_instances[serie_ID].grid(row=i, column=0, sticky='news')
        
        # Update buttons frames idle tasks to let tkinter calculate frame sizes
        self.update_idletasks()
        # Update te scrollbars
        self.canvas.config(scrollregion=self.canvas.bbox("all"))

    def reset_preview_frames(self):
        logging.warning("reset_preview_frames: ", self.DICOM_serie_instances) 
        for serie_ID in self.DICOM_serie_instances:
            self.DICOM_serie_instances[serie_ID].destroy()
        self.set_preview_frames()

    def get_serie_length(self, serie_ID):
        return self.DICOM_serie_instances[serie_ID].get_serie_length()
    
    def get_image_slice(self, serie_ID, slice_index):
        return self.DICOM_serie_instances[serie_ID].get_image_slice(slice_index)
    
    def get_serie_size(self, serie_ID):
        return self.DICOM_serie_instances[serie_ID].get_serie_size()
    
    def get_serie_image(self, serie_ID):
        return self.DICOM_serie_instances[serie_ID].get_serie_image()