import tkinter as tk  
from tkinter import ttk, Label, Menu, filedialog
import logging
import numpy as np
from PIL import Image, ImageTk
import math

from ITKviewerframe import ITKviewerFrame

from timeit import default_timer as timer

def timer_func(func):
    def wrapper(*args, **kwargs):
        t1 = timer()
        result = func(*args, **kwargs)
        t2 = timer()
        print(f'{func.__name__}() executed in {(t2-t1):.6f}s')
        return result
    return wrapper

class ITKsegmentationFrame(ITKviewerFrame):
    def __init__(self, mainframe, **kwargs):
        """ Initialize the ITK viewer Frame """
        self.max_layers = 255
        super().__init__(mainframe, **kwargs)
        self.mainframe = mainframe
        
        self.seg_image = ImageTk.PhotoImage(self.get_image_from_seg_array())

    def initialize(self):
        self.NP_seg_array = np.empty((50,512,512, self.max_layers), dtype=bool)
        self.image_segmentation = Image.fromarray(np.zeros((self.NP_seg_array.shape[1], self.NP_seg_array.shape[2], 4), dtype=np.uint8))
        super().initialize()
    
    def load_new_CT(self, np_DICOM_array: np.ndarray):
        """placeholder"""
        self.NP_seg_array = np.empty(np_DICOM_array.shape + (self.max_layers,), dtype=bool)
        super().load_new_CT(np_DICOM_array)
    
    @timer_func
    def get_image_from_seg_array(self):
        """placeholder"""
        image_segmentation_array = np.zeros((self.NP_seg_array.shape[1], self.NP_seg_array.shape[2], 4), dtype=np.uint8)
        # NP_seg_array_combined = np.amax(self.NP_seg_array[self.slice_index,: , :, :], axis=-1)
        # image_segmentation_array[NP_seg_array_combined != 0] = [255, 0, 0, 125]

        NP_seg_array_combined = self.NP_seg_array[self.slice_index, :, :, :].argmax(axis=-1)
        image_segmentation_array[self.NP_seg_array[self.slice_index, :, :, 0] == True] = [255, 0, 0, 125]
        image_segmentation_array[NP_seg_array_combined == 1] = [0, 255, 0, 125]
        image_segmentation_array[NP_seg_array_combined == 2] = [0, 0, 255, 125]
        image_segmentation_array[NP_seg_array_combined == 3] = [255, 255, 0, 125]
        image_segmentation_array[NP_seg_array_combined == 4] = [255, 0, 255, 125]
        image_segmentation_array[NP_seg_array_combined == 5] = [0, 255, 255, 125]

        self.image_segmentation = Image.fromarray(image_segmentation_array, "RGBA")
        return self.image_segmentation

    def zoom_at(self, img, x=0, y=0, zoom=1, interpolate=Image.LANCZOS):
        """ Zoom at x,y location"""
        CT_image = img.convert('RGBA')
        seg_image = self.get_image_from_seg_array()
        result = Image.alpha_composite(CT_image, seg_image)
        return super().zoom_at(result, x, y, zoom, interpolate)

    def button1_press_event_image(self, x, y):
        return 

