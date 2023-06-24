import tkinter as tk  
from tkinter import ttk, Label, Menu, filedialog
import logging
import numpy as np
from PIL import Image, ImageTk
import math
import SimpleITK as sitk

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
        self.NP_seg_array = sitk.Image(self.ITK_image.GetSize(), sitk.sitkUInt8)
        super().initialize()
    
    def load_new_CT(self, np_DICOM_array: np.ndarray, window: int = 500, level: int = 1000, ITK_image: sitk.Image = None,**kwargs):
        """placeholder"""
        self.seg_image_needs_update = True
        self.NP_seg_array = sitk.Image(ITK_image.GetSize(), sitk.sitkUInt8)
        super().load_new_CT(np_DICOM_array, window, level, **kwargs)
    
    @timer_func(FPS_target=6000)
    def get_image_from_seg_array(self):
        """placeholder"""
        image_segmentation_array = sitk.GetArrayFromImage(sitk.LabelToRGB(self.NP_seg_array[:,:, self.slice_index]))

        return Image.fromarray(image_segmentation_array, "RGB")

    @timer_func(FPS_target=60)
    def zoom_itk(self, *args, **kwargs):
        """ Zoom at x,y location"""
        combined = sitk.LabelOverlay(self.slice_gray_image, self.NP_seg_array[:,:, self.slice_index])

        euler2d = sitk.Euler2DTransform()
        # Why do we set the center?
        
        output_spacing = [1/self.zoom ,1 /self.zoom]
        # Identity cosine matrix (arbitrary decision).
        output_direction = [1.0, 0.0, 0.0, 1.0]
        # Minimal x,y coordinates are the new origin.
        output_origin = [self.center_X, self.center_Y]
        # Compute grid size based on the physical size and spacing.
        output_size = [self.image_label.winfo_width(), self.image_label.winfo_height()]

        resampled_image = sitk.Resample(
            combined,
            output_size,
            euler2d,
            sitk.sitkNearestNeighbor,
            output_origin,
            output_spacing,
            output_direction,
        )
        self.seg_image = resampled_image
        return Image.fromarray( sitk.GetArrayFromImage(self.seg_image).astype(np.uint8), mode="RGB")
        

    def button1_press_event_image(self, x, y):
        return 


    def set_segmentation_point_current_slice(self, x, y, layer_height):
        self.NP_seg_array[x, y, self.slice_index] = layer_height
        self.seg_image_needs_update = True
        self.update_image()

    def set_segmentation_mask_current_slice(self, layer_height, mask: np.ndarray):
        self.NP_seg_array[:, :, self.slice_index] = mask
        self.seg_image_needs_update = True
        self.update_image()

    def clear_segmentation_mask_current_slice(self, layer_height = None):
        if layer_height is None:
            self.NP_seg_array[:, :, self.slice_index] = 0
        else:
            self.NP_seg_array[self.NP_seg_array == layer_height] = 0
        self.seg_image_needs_update = True
        self.update_image()

    def next_slice(self):
        self.seg_image_needs_update = True
        return super().next_slice()
    
    def previous_slice(self):
        self.seg_image_needs_update = True
        return super().previous_slice()
