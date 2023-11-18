import tkinter as tk  
from tkinter import ttk, Label, Menu, filedialog
import logging
import numpy as np
from PIL import Image, ImageTk
import math
from Utils import timer_func, PatchedFrame
import SimpleITK as sitk
from ITKviewerframe import ITKviewerFrame
from ITKsegmentationframe import ITKsegmentationFrame
import asyncio

example = [
    [[1,
      2],3,],
    4,
    5,
]
panedwindows = False #needs more work to be functional
example_frame_list = [
    [[ITKsegmentationFrame,
      ITKviewerFrame],ITKviewerFrame,],
    ITKviewerFrame,
    ITKsegmentationFrame,
]

example_dual_frame_list = [ITKsegmentationFrame, ITKviewerFrame]

example_segmentation_frame_list = [ITKsegmentationFrame,ITKsegmentationFrame]
example_only_frame_list = [ITKviewerFrame,ITKviewerFrame]

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

def create_image_viewers_from_nested_list(mainframe, nested_list, horizontal= True, position = 0, FrameManager = None, threading = False, **kwargs):
    """placeholder"""
    
    if panedwindows:
        frame = ttk.Panedwindow(mainframe, orient= tk.HORIZONTAL if horizontal else tk.VERTICAL, width=20, height=20)
    else:
        frame = PatchedFrame(mainframe, **kwargs)
    
    if panedwindows:
        mainframe.add(frame)
        
    else:
        if horizontal:
            frame.grid(row=position, column=0, sticky="news")
        else:
            frame.grid(row=0, column=position, sticky="news")
    
    result = []
    for i, sub_item in enumerate(nested_list):
        if isinstance(sub_item, list): 
            result_sublist = create_image_viewers_from_nested_list(frame, sub_item, horizontal= not horizontal, position = i, FrameManager = FrameManager, threading = threading, **kwargs)
            result += [result_sublist]
        else:
            image_frame = sub_item(frame, FrameManager=FrameManager, threading = threading, **kwargs)
            image_frame.grid_propagate(0) #not essential when grid is used correctly else the frames will grow indefinitely or "attacking" each other
            
            if panedwindows:
                if horizontal:
                    frame.add(image_frame)
                else:
                    frame.add(image_frame)
            else:
                if horizontal:
                    image_frame.grid(row=0, column=i, sticky="news", padx=1, pady=1)
                else:
                    image_frame.grid(row=i, column=0, sticky="news", padx=1, pady=1)
            
            result += [image_frame]
    
    if panedwindows:
        pass
        # if horizontal:
        #     frame.columnconfigure(tuple([n for n in range(0, i+1)]), weight=1)
        #     frame.rowconfigure(0, weight=1)
        # else:
        #     frame.rowconfigure(tuple([n for n in range(0, i+1)]), weight=1)
        #     frame.columnconfigure(0, weight=1)
    else:
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
            sub_item.update_image()
        
async def update_images_if_needed_from_nested_list(nested_list, horizontal= True, **kwargs):
    frame = nested_list[0]
    for i, sub_item in enumerate(nested_list[1:]):
        if isinstance(sub_item, list):
            update_images_if_needed_from_nested_list(sub_item, horizontal= not horizontal, **kwargs)
        else:
            asyncio.get_running_loop().create_task(sub_item.update_image_if_needed())

def get_first_frame_from_nested_list(nested_list):
    for sub_item in nested_list[1:]:
        if isinstance(sub_item, list):
            return get_first_frame_from_nested_list(sub_item)
        else:
            return sub_item


class imagesFrameManager(ttk.PanedWindow):
    def __init__(self, mainframe, image_label_layout: list = [0], parent = None, threading = False, **kwargs):
        """ Initialize the ITK viewer Frame """
        super().__init__(mainframe)
        self.parent = parent
        
        self.frame = self
        self.frame.grid(row=0, column=0, sticky= tk.N + tk.S + tk.E + tk.W)
        self.frame.bind('<Configure>', lambda event: self.update_configure())

        # self.frame.rowconfigure(tuple([n for n in range(len(image_label_layout))]), weight=1)
        self.frame.rowconfigure(0, weight=1)
        # self.frame.columnconfigure(tuple([n for n in range(len(image_label_layout[0]))]), weight=1)
        self.frame.columnconfigure(0, weight=1)

        self.images_labels = create_image_viewers_from_nested_list(self.frame, image_label_layout, FrameManager = self, threading = threading, **kwargs)
        self.active_widget = get_first_frame_from_nested_list(self.images_labels)
        self.active_widget.focus_set()
        # self.active_widget.on_focus_in()

        self.series_IDs = None
    
    def set_active_widget(self, widget):
        """placeholder"""
        if self.active_widget == widget:
            logging.warning("widget is already active")
            return
        if self.active_widget is not None:
            self.active_widget.on_focus_out()
        widget.focus_set()
        self.active_widget = widget

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

    async def update_image_if_needed(self) -> None:
        await update_images_if_needed_from_nested_list(self.images_labels)
        
    def update_configure(self):
        self.frame.update_idletasks()
        self.frame.update()
        # update_image_viewer_frames_from_nested_list(self.images_labels)
        update_ITKviewerFrames_from_nested_list(self.images_labels)
        self.active_widget.focus_set()
        """placeholder"""
