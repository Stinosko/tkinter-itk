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

def create_concept_from_nested_list(mainframe, nested_list, horizontal= True, **kwargs):
    """placeholder"""
    result = []
    for i, sub_item in enumerate(nested_list):
        if isinstance(sub_item, list): 
            result_sublist = create_concept_from_nested_list(mainframe, sub_item, not horizontal)
            result += [result_sublist]
        else:
            result += [1]
    return result

def create_image_viewers_from_nested_list(mainframe, nested_list, horizontal= True, position = 0, **kwargs):
    """placeholder"""
    frame = PatchedFrame(mainframe, **kwargs)
    if horizontal:
        frame.grid(row=position, column=0, sticky="news")
    else:
        frame.grid(row=0, column=position, sticky="news")
    
    result = []
    for i, sub_item in enumerate(nested_list):
        if isinstance(sub_item, list): 
            result_sublist = create_image_viewers_from_nested_list(frame, sub_item, horizontal= not horizontal, position = i, **kwargs)
            result += [result_sublist]
        else:
            image_frame = ITKviewerFrame(frame, mainframe, **kwargs)
            image_frame.grid_propagate(0) #not essential when grid is used correctly else the frames will grow indefinitely or "attacking" each other
            if horizontal:
                image_frame.grid(row=0, column=i, sticky="news", padx=1, pady=1)
            else:
                image_frame.grid(row=i, column=0, sticky="news", padx=1, pady=1)
            result += [image_frame]
    if horizontal:
        frame.columnconfigure(tuple([n for n in range(0, i+1)]), weight=1)
        frame.rowconfigure(0, weight=1)
    else:
        frame.rowconfigure(tuple([n for n in range(0, i+1)]), weight=1)
        frame.columnconfigure(0, weight=1)
    return [frame] + result

def update_image_viewer_frames_from_nested_list(nested_list, horizontal= True, position = 0, **kwargs):
    frame = nested_list[0]
    for i, sub_item in enumerate(nested_list[1:]):
        if isinstance(sub_item, list):
            update_image_viewer_frames_from_nested_list(sub_item, horizontal= not horizontal, position = i, **kwargs)
        else:
            sub_item.columnconfigure(0, weight=1)
            sub_item.rowconfigure(0, weight=1)
            sub_item.frame.columnconfigure(0, weight=1)
            sub_item.frame.rowconfigure(0, weight=1)
            sub_item.image_label.columnconfigure(0, weight=1)
            sub_item.image_label.rowconfigure(0, weight=1)
            sub_item.update_image()
    if frame is not None:
        if horizontal:
            frame.columnconfigure(tuple([n for n in range(0, i+1)]), weight=1)
            frame.rowconfigure(0, weight=1)
        else:
            frame.rowconfigure(tuple([n for n in range(0, i+1)]), weight=1)
            frame.columnconfigure(0, weight=1)
    else:
        print("Error: no frame found")

def update_ITKviewerFrames_from_nested_list(nested_list, horizontal= True, **kwargs):
    frame = nested_list[0]
    for i, sub_item in enumerate(nested_list[1:]):
        if isinstance(sub_item, list):
            update_ITKviewerFrames_from_nested_list(sub_item, horizontal= not horizontal, **kwargs)
        else:
            sub_item.columnconfigure(0, weight=1)
            sub_item.rowconfigure(0, weight=1)
            sub_item.frame.columnconfigure(0, weight=1)
            sub_item.frame.rowconfigure(0, weight=1)
            sub_item.image_label.columnconfigure(0, weight=1)
            sub_item.image_label.rowconfigure(0, weight=1)
            sub_item.update_image()
        

class imagesFrameManager(PatchedFrame):
    def __init__(self, mainframe, image_label_layout: list = [0], **kwargs):
        """ Initialize the ITK viewer Frame """
        super().__init__(mainframe, **kwargs)
        self.mainframe = mainframe
        
        self.frame = PatchedFrame(self)
        self.frame.grid(row=0, column=0, sticky= tk.N + tk.S + tk.E + tk.W)
        self.frame.bind('<Configure>', lambda event: self.update_configure())

        # self.frame.rowconfigure(tuple([n for n in range(len(image_label_layout))]), weight=1)
        self.frame.rowconfigure(0, weight=1)
        # self.frame.columnconfigure(tuple([n for n in range(len(image_label_layout[0]))]), weight=1)
        self.frame.columnconfigure(0, weight=1)

        self.images_labels = create_image_viewers_from_nested_list(self.frame, image_label_layout, **kwargs)


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

        
    def update_configure(self):
        self.frame.update_idletasks()
        self.frame.update()
        update_image_viewer_frames_from_nested_list(self.images_labels)
        update_ITKviewerFrames_from_nested_list(self.images_labels)
        """placeholder"""
