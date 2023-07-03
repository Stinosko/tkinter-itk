import tkinter as tk  
from tkinter import ttk, Label, Menu, filedialog
import logging
import numpy as np
from PIL import Image, ImageTk
import math
from Utils import timer_func, PatchedFrame
import SimpleITK as sitk
from ITKviewerframe import ITKviewerFrame

example = [
    [[1,
      2],3,],
    4,
    5,
]

def find_id_in_nested_list(mylist, char):
    for i, sub_item in enumerate(mylist):
        if isinstance(sub_item, list): 
            result = find_id_in_nested_list(sub_item, char)
            if result is not None:
                return [i] + result
            else:
                continue
        if char == sub_item:
            return [i]
    return None

class ImagesFrameManager(PatchedFrame):
    def __init__(self, mainframe, image_label_layout: list = [0], **kwargs):
        """ Initialize the ITK viewer Frame """
        super().__init__(mainframe, **kwargs)
        self.mainframe = mainframe
        
        self.frame = tk.Frame(self)
        self.frame.grid(row=0, column=0, sticky="news")

        self.images_labels = np.empty(image_label_layout, dtype=ITKviewerFrame)
        for x in range(image_label_layout[0]):
            for y in range(image_label_layout[1]):
                self.images_labels[x,y] = ITKviewerFrame(self.frame, self, sticky="news")
                self.images_labels[x,y].grid(row=x, column=y, sticky="news", padx=1, pady=1)

        self.active_image_x = 0
        self.active_image_y = 0

        self.series_IDs = None
    
    def set_ImageSeries(self, data_directory: str = "", series_IDs: sitk.ImageSeriesReader = None):
        """placeholder"""
        self.series_IDs = series_IDs
        size_series = len(series_IDs)

        for x in range(self.images_labels.shape[0]):
            for y in range(self.images_labels.shape[1]):
                if x*y > size_series:
                    break
                self.images_labels[x,y].set_ImageSeries(sitk.ImageSeriesReader_GetGDCMSeriesFileNames(
            data_directory, series_IDs[x*y]))

        