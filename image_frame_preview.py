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
import re

def retag(tag, widget):
    "Binds an tag to a widget and all its descendants."
    widget.bindtags((tag,) + widget.bindtags())
    for child in widget.children.values():
        retag(tag, child)

def clone_widget(widget, master=None):
    """
    https://stackoverflow.com/questions/46505982/is-there-a-way-to-clone-a-tkinter-widget
    Create a cloned version o a widget

    Parameters
    ----------
    widget : tkinter widget
        tkinter widget that shall be cloned.
    master : tkinter widget, optional
        Master widget onto which cloned widget shall be placed. If None, same master of input widget will be used. The
        default is None.

    Returns
    -------
    cloned : tkinter widget
        Clone of input widget onto master widget.

    """
    # Get main info
    parent = master if master else widget.master
    cls = widget.__class__

    # Clone the widget configuration
    cfg = {key: widget.cget(key) for key in widget.configure()}
    cloned = cls(parent, **cfg)

    # Clone the widget's children
    for child in widget.winfo_children():
        child_cloned = clone_widget(child, master=cloned)
        if child.grid_info():
            grid_info = {k: v for k, v in child.grid_info().items() if k not in {'in'}}
            child_cloned.grid(**grid_info)
        elif child.place_info():
            place_info = {k: v for k, v in child.place_info().items() if k not in {'in'}}
            child_cloned.place(**place_info)
        else:
            pack_info = {k: v for k, v in child.pack_info().items() if k not in {'in'}}
            child_cloned.pack(**pack_info)

    return cloned

class image_frame_preview(PatchedFrame):
    """placeholder"""
    def __init__(self, mainframe, DICOM_DIR, Serie_ID, reader, **kwargs):
        PatchedFrame.__init__(self, mainframe, **kwargs)
        self.mainframe = mainframe
        self.DICOM_DIR = DICOM_DIR
        self.Serie_ID = Serie_ID
        self.reader = reader

        slices = len(self.reader.GetFileNames())
        self.preview_reader = sitk.ImageFileReader()
        self.preview_reader.SetFileName(self.reader.GetFileNames()[round(slices/2) - 1])
        self.preview_ITK_image = self.preview_reader.Execute()
        self.preview_image = sitk.GetArrayFromImage(self.preview_ITK_image)

        self.preview_image = self.preview_image[0,:,:]
        self.preview_image = self.preview_image.astype(np.uint8)
        self.preview_image = Image.fromarray(self.preview_image)
        self.preview_image = ImageTk.PhotoImage(self.preview_image)

        self.preview_label = Label(self, image=self.preview_image, width=150, height=150)
        self.preview_label.grid(row=0, column=0, sticky='w')
        self.config(width=125)

        self.button = ttk.Button(self, text=self.preview_reader.GetMetaData(key = "0020|000e"))
        self.button.grid(row=1, column=0)

        self.make_draggable()

    def make_draggable(self):
        retag("drag",self)
        self._nametowidget(".").bind_class("drag","<ButtonPress-1>", self.on_drag_start)
        self._nametowidget(".").bind_class("drag","<B1-Motion>", self.on_drag_motion)
        self._nametowidget(".").bind_class("drag","<ButtonRelease-1>", self.on_drag_release)

    def on_drag_start(self, event):
        image_frame_preview = re.search("(.*)(image_frame_preview)(\\d+)?", str(event.widget)).group()
        self.drag_widget = clone_widget(self._nametowidget(image_frame_preview).preview_label, master=self._nametowidget("."))
        self.drag_widget.reader = self._nametowidget(image_frame_preview).reader
        self.drag_widget._drag_start_x = event.x
        self.drag_widget._drag_start_y = event.y
    
    def on_drag_motion(self, event):
        x = event.x_root - self._nametowidget(".").winfo_rootx() - int(self.drag_widget.winfo_width() / 2)
        y = event.y_root - self._nametowidget(".").winfo_rooty() + 2
        
        self.drag_widget.place(x=x, y=y)
        

    def on_drag_release(self, event):
        x = event.widget.winfo_x() + event.x + self._nametowidget(".").winfo_rootx()
        y = event.widget.winfo_y() + event.y + self._nametowidget(".").winfo_rooty()
        self.drag_widget.place_forget()

        self._nametowidget(".").update_idletasks()
        target_widget = self._nametowidget(".").winfo_containing(x,y)
        itkviewerframe = re.search("(.*)(itkviewerframe)(\\d+)?", str(target_widget)).group()
        print(itkviewerframe)
        itkviewerframe = self._nametowidget(itkviewerframe)
        ITK_image = self.drag_widget.reader.Execute()
        ITK_image.SetDirection((1,0,0,0,1,0,0,0,1))
        itkviewerframe.load_new_CT(ITK_image= ITK_image)
