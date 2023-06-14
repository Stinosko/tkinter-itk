import tkinter as tk  
from tkinter import ttk, Label, Menu, filedialog
import logging
import numpy as np
from PIL import Image, ImageTk
import math

from ITKviewerframe import ITKviewerFrame
from Utils import timer_func


class ITKsegmentationFrame(ITKviewerFrame):
    def __init__(self, mainframe, **kwargs):
        """ Initialize the ITK viewer Frame """
        self.max_layers = 255
        self.seg_image_needs_update = True
        super().__init__(mainframe, **kwargs)
        self.mainframe = mainframe
        self.seg_image = ImageTk.PhotoImage(self.get_image_from_seg_array())

    def initialize(self):
        self.NP_seg_array = np.empty((50,512,512, self.max_layers), dtype=bool)
        self.image_segmentation = Image.fromarray(np.zeros((self.NP_seg_array.shape[1], self.NP_seg_array.shape[2], 4), dtype=np.uint8))
        super().initialize()
    
    def load_new_CT(self, np_DICOM_array: np.ndarray):
        """placeholder"""
        self.seg_image_needs_update = True
        self.NP_seg_array = np.empty(np_DICOM_array.shape + (self.max_layers,), dtype=bool)
        super().load_new_CT(np_DICOM_array)
    
    
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

    @timer_func(FPS_target=60)
    def zoom_at(self, img, x=0, y=0, zoom=1, interpolate=Image.LANCZOS):
        """ Zoom at x,y location"""
        CT_image = img.convert('RGBA')
        if self.seg_image_needs_update:
            self.seg_image = self.get_image_from_seg_array()
            self.seg_image_needs_update = False
        result = Image.alpha_composite(CT_image, self.seg_image)
        return super().zoom_at(result, x, y, zoom, interpolate)

    def button1_press_event_image(self, x, y):
        return 


    def set_segmentation_point_current_slice(self, x, y, layer_height, value: bool):
        self.NP_seg_array[self.slice_index, y, x, layer_height] = value
        self.seg_image_needs_update = True
        self.update_image()

    def set_segmentation_mask_current_slice(self, layer_height, mask: np.ndarray):
        self.NP_seg_array[self.slice_index, :, :, layer_height] = mask
        self.seg_image_needs_update = True
        self.update_image()

    def clear_segmentation_mask_current_slice(self, layer_height = None):
        if layer_height is None:
            self.NP_seg_array[self.slice_index, :, :, :] = False
        else:
            self.NP_seg_array[self.slice_index, :, :, layer_height] = False
        self.seg_image_needs_update = True
        self.update_image()

    def next_slice(self):
        self.seg_image_needs_update = True
        return super().next_slice()
    
    def previous_slice(self):
        self.seg_image_needs_update = True
        return super().previous_slice()
