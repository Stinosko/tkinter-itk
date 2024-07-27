import os
import logging
import tkinter as tk  
import SimpleITK as sitk
from .DICOM_serie_instance import DICOM_serie_instance
from .DICOM_serie_instance_sitk import DICOM_serie_instance_sitk
from ..Utils import PatchedFrame


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
        self.scrollable_frame = tk.Frame(self.canvas, bg="blue")
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor='nw')
        
        self.DICOM_serie_instances = {}
        self.series_file_names = {}
        

    def load_DICOM_serie(self, DICOM_DIR = None, image_name = None) -> None:
        """ load a DICOM serie from a directory """
        logging.warning(f"Not implemented: {self.__class__.__name__}.load_DICOM_serie")

    def load_image_serie(self, image, image_name, add = False):
        """ load a serie from a SimpleITK image """
        logging.warning(f"Not implemented: {self.__class__.__name__}.load_image_serie")

    def get_serie_IDs(self):
        return self.DICOM_serie_instances.keys()

    def set_preview_frames(self):
        # Add 9-by-5 buttons to the frame
        
        self.DICOM_serie_instances = {}
        for i, serie_ID in enumerate(self.get_serie_IDs()):
            self.DICOM_serie_instances[serie_ID] = DICOM_serie_instance_sitk(self.scrollable_frame, serie_ID, self.get_serie_reader(serie_ID))
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
        if serie_ID not in self.DICOM_serie_instances:
            logging.warning(f"Serie ID {serie_ID} does not exist")
            return None
        return self.DICOM_serie_instances[serie_ID].get_image_slice(slice_index)
    
    def get_serie_size(self, serie_ID):
        return self.DICOM_serie_instances[serie_ID].get_serie_size()
    
    def get_serie_image(self, serie_ID):
        return self.DICOM_serie_instances[serie_ID].get_serie_image()
    
    def load_serie(self, serie_ID):
        return self.DICOM_serie_instances[serie_ID].load_serie()
    
    def unload_serie(self, serie_ID):
        return self.DICOM_serie_instances[serie_ID].unload_serie()
    
    def get_total_slices(self, serie_ID):
        return self.DICOM_serie_instances[serie_ID].get_total_slices()  
    
    def get_dicom_value(self, serie_ID, key = None, pytag = None, slice_index = 0):
        """ get a DICOM value from a serie 
        serie_ID: serie ID
        key: DICOM key, ex "0008|103e" (SeriesDescription)
        pytag: pydicom tag, ex "SeriesDescription"
        """
        if serie_ID not in self.DICOM_serie_instances:
            logging.warning(f"Serie ID {serie_ID} does not exist")
            return None

        if key is None and pytag is None:
            logging.warning("key and pytag are None")
            return None
        
        return self.DICOM_serie_instances[serie_ID].get_dicom_value(key, pytag, slice_index)