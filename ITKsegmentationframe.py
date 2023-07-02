import tkinter as tk  
from tkinter import ttk, Label, Menu, filedialog
import logging
import numpy as np
from PIL import Image, ImageTk
import math
import SimpleITK as sitk
from reloading import reloading

from ITKviewerframe import ITKviewerFrame
from Utils import timer_func

def set_mask_value(image, mask, value):
    msk32 = sitk.Cast(mask, sitk.sitkFloat32)
    msk32.CopyInformation(image)
    return sitk.Cast(sitk.Cast(image, sitk.sitkFloat32) *
                     sitk.InvertIntensity(msk32, maximum=1.0) + 
                     msk32*value, image.GetPixelID())

class ITKsegmentationFrame(ITKviewerFrame):
    def __init__(self, mainframe, **kwargs):
        """ Initialize the ITK viewer Frame """
        self.max_layers = 255
        self.seg_image_needs_update = True
        super().__init__(mainframe, **kwargs)
        self.mainframe = mainframe
        self.seg_image = ImageTk.PhotoImage(self.get_image_from_seg_array())

    def initialize(self):
        self.ITK_seg_array = sitk.Image(self.ITK_image.GetSize(), sitk.sitkUInt8)
        self.ITK_seg_array.CopyInformation(self.ITK_image)
        super().initialize()
    
    def load_new_CT(self, window: int = 600, level: int = 301, ITK_image: sitk.Image = None,**kwargs):
        """placeholder"""
        self.seg_image_needs_update = True
        self.ITK_seg_array = sitk.Image(ITK_image.GetSize(), sitk.sitkUInt8)
        self.ITK_seg_array.CopyInformation(ITK_image)
        super().load_new_CT(window, level, ITK_image= ITK_image, **kwargs)
    
    @timer_func(FPS_target=6000)
    def get_image_from_seg_array(self):
        """placeholder"""
        image_segmentation_array = sitk.GetArrayFromImage(sitk.LabelToRGB(self.ITK_seg_array[:,:, self.slice_index]))

        return Image.fromarray(image_segmentation_array, "RGB")

    
    def zoom_itk(self, *args, **kwargs):
        """ Zoom at x,y location"""
        NP_seg_slice = self.ITK_seg_array[:,:, self.slice_index]
        NP_seg_slice.CopyInformation(self.slice_gray_ITK_image)
        self.slice_ITK_image = sitk.LabelOverlay(self.slice_gray_ITK_image, NP_seg_slice, opacity=0.8)
        return super().zoom_itk(*args, **kwargs)        

    def button1_press_event_image(self, x, y):
        return 


    def set_segmentation_point_current_slice(self, x, y, layer_height):
        self.ITK_seg_array[x, y, self.slice_index] = layer_height
        self.seg_image_needs_update = True
        self.update_image()

    def set_segmentation_mask_current_slice(self, layer_height: int, mask: np.ndarray):
        
        self.ITK_seg_array[:, :, self.slice_index] = set_mask_value(self.ITK_seg_array[:, :, self.slice_index], mask, layer_height) 
        self.seg_image_needs_update = True
        self.update_image()

    def clear_segmentation_mask_current_slice(self, layer_height = None):
        if layer_height is None:
            self.ITK_seg_array[:, :, self.slice_index] = 0
        else:
            self.ITK_seg_array[:, :, self.slice_index] = set_mask_value(self.ITK_seg_array[:, :, self.slice_index], self.ITK_seg_array[:, :, self.slice_index] == layer_height, 0)
        self.seg_image_needs_update = True
        self.update_image()

    def next_slice(self):
        self.seg_image_needs_update = True
        return super().next_slice()
    
    def previous_slice(self):
        self.seg_image_needs_update = True
        return super().previous_slice()

    def get_NP_seg_slice(self):
        return sitk.GetArrayFromImage(self.ITK_seg_array[:,:, self.slice_index])
    
