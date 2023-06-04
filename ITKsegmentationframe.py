import tkinter as tk  
from tkinter import ttk, Label, Menu, filedialog
import logging
import numpy as np
from PIL import Image, ImageTk
import math

from ITKviewerframe import ITKviewerFrame

class ITKsegmentationFrame(ITKviewerFrame):
    def __init__(self, mainframe, **kwargs):
        """ Initialize the ITK viewer Frame """
        super().__init__(mainframe, **kwargs)
        self.mainframe = mainframe
        self.seg_image = ImageTk.PhotoImage(self.get_image_from_seg_array())

    def initialize(self):
        self.NP_seg_array = np.empty((50,512,512))
        self.image_segmentation = Image.fromarray(np.zeros((self.NP_seg_array.shape[1], self.NP_seg_array.shape[2], 4), dtype=np.uint8))
        super().initialize()
    
    def load_new_CT(self, np_DICOM_array: np.ndarray):
        """placeholder"""
        self.NP_seg_array = np.empty(np_DICOM_array.shape)
        super().load_new_CT(np_DICOM_array)
    
    def get_image_from_seg_array(self):
        """placeholder"""
        image_segmentation_array = np.zeros((self.NP_seg_array.shape[1], self.NP_seg_array.shape[2], 4), dtype=np.uint8)
        image_segmentation_array[self.NP_seg_array[self.slice_index,: , :] == 1] = [255, 0, 0, 255]
        self.image_segmentation = Image.fromarray(image_segmentation_array, "RGBA")
        return self.image_segmentation

    def zoom_at(self, img, x=0, y=0, zoom=1, interpolate=Image.LANCZOS):
        """ Zoom at x,y location"""
        CT_image = img.convert('RGBA')
        seg_image = self.get_image_from_seg_array()
        result = Image.alpha_composite(CT_image, seg_image)
        return super().zoom_at(result, x, y, zoom, interpolate)

    def button1_press_event_image(self, x, y):
        self.NP_seg_array[self.slice_index, int(x), int(y)] = 1
        self.update_image()

