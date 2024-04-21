import re
import logging 
from tkinter import ttk, Label
import numpy as np
import tkinter as tk 
import SimpleITK as sitk
from PIL import Image, ImageTk
from .Utils import PatchedFrame

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

def normalize_np_array_between_0_and_255(np_array):
    minimum_hu = np_array.min()
    maximum_hu  = np_array.max()
    
    np_array[np_array < minimum_hu] = minimum_hu
    np_array[np_array > maximum_hu] = maximum_hu
    np_array = np.divide(np_array - np_array.min(), (np_array.max() - np_array.min()))*255
    np_array = np_array.astype(np.uint8)
    return np_array

class DICOM_serie_instance(PatchedFrame):
    """placeholder"""
    def __init__(self, mainframe, DICOM_DIR, serie_ID, reader, **kwargs):
        PatchedFrame.__init__(self, mainframe, **kwargs)
        self.mainframe = mainframe
        self.DICOM_DIR = DICOM_DIR
        self.serie_ID = serie_ID
        self.reader = reader
        self.ITK_image = None # preserving RAM if entire serie is not needed

        if self.reader.GetImageIO() == "":
            self.total_slices = len(self.reader.GetFileNames())
            self.preview_reader = sitk.ImageFileReader()
            self.preview_reader.SetFileName(self.reader.GetFileNames()[round(self.total_slices/2) - 1])
            self.preview_ITK_image = self.preview_reader.Execute()
            

            self.preview_image = sitk.GetArrayFromImage(self.preview_ITK_image)
            self.preview_image = normalize_np_array_between_0_and_255(self.preview_image[0,:,:])
            self.preview_image = self.preview_image.astype(np.uint8)
            self.preview_image = Image.fromarray(self.preview_image)
            self.preview_image = ImageTk.PhotoImage(self.preview_image)

        else:
            self.ITK_image = self.reader.Execute()
            if self.ITK_image.GetDimension() == 4:
                self.ITK_image = self.ITK_image[:,:,:,0]
            elif self.ITK_image.GetDimension() > 4:
                logging.error("Image dimension is greater than 4. Cannot be displayed.")
                raise ValueError("Image dimension is greater than 4. Cannot be displayed.")
            elif self.ITK_image.GetDimension() == 2:
                self.ITK_image = sitk.JoinSeries([self.ITK_image])
            elif self.ITK_image.GetDimension() == 3:
                pass
            elif self.ITK_image.GetDimension() == 1:
                logging.error("Image dimension is less than 2. Cannot be displayed.")
                raise ValueError("Image dimension is less than 2. Cannot be displayed.")
            
            self.ITK_image.SetDirection((1,0,0,0,1,0,0,0,1))
            self.ITK_image.SetOrigin((0,0,0))
            self.total_slices = self.ITK_image.GetSize()[-1]
            self.preview_reader = None
            self.preview_ITK_image = None

            self.preview_image = sitk.GetArrayFromImage(self.ITK_image[:,:,round(self.total_slices/2) - 1])
            
            self.preview_image = normalize_np_array_between_0_and_255(self.preview_image)
            self.preview_image = self.preview_image.astype(np.uint8)
            self.preview_image = Image.fromarray(self.preview_image)
            self.preview_image = ImageTk.PhotoImage(self.preview_image)

        self.preview_label = Label(self, image=self.preview_image, width=150, height=150)
        self.preview_label.grid(row=0, column=0, sticky='w')
        self.config(width=125)

        self.button = ttk.Button(self, text=self.serie_ID)
        self.button.grid(row=1, column=0)

        self.make_draggable()

    def make_draggable(self):
        retag("drag",self)
        self._nametowidget(".").bind_class("drag","<ButtonPress-1>", self.on_drag_start)
        self._nametowidget(".").bind_class("drag","<B1-Motion>", self.on_drag_motion)
        self._nametowidget(".").bind_class("drag","<ButtonRelease-1>", self.on_drag_release)

    def on_drag_start(self, event):
        DICOM_serie_instance = re.search("(.*)(DICOM_serie_instance)(\\d+)?".lower(), str(event.widget)).group()
        self.drag_widget = clone_widget(self._nametowidget(DICOM_serie_instance).preview_label, master=self._nametowidget("."))
        self.drag_widget.serie_ID = self._nametowidget(DICOM_serie_instance).serie_ID
        self.drag_widget.ITK_image = self._nametowidget(DICOM_serie_instance).ITK_image
        # print(self.drag_widget.serie_ID)
        self.drag_widget._drag_start_x = event.x
        self.drag_widget._drag_start_y = event.y
    
    def on_drag_motion(self, event):
        x = event.x_root - self._nametowidget(".").winfo_rootx() - int(self.drag_widget.winfo_width() / 2)
        y = event.y_root - self._nametowidget(".").winfo_rooty() + 2
        
        self.drag_widget.place(x=x, y=y)
        

    def on_drag_release(self, event):
        x = event.x_root
        y = event.y_root
        self.drag_widget.place_forget()

        self._nametowidget(".").update_idletasks()
        target_widget = self._nametowidget(".").winfo_containing(x,y)
        
        itkviewerframe = re.search("(.*)(itkviewerframe|itksegmentationframe)(\\d+)?".lower(), str(target_widget))
        if itkviewerframe is None:
            return
        itkviewerframe = itkviewerframe.group()
        logging.debug(f"Target widget: {itkviewerframe}")
        itkviewerframe = self._nametowidget(itkviewerframe)
        serie_ID = self.drag_widget.serie_ID
        ITK_image = self.drag_widget.ITK_image
        itkviewerframe.load_new_CT(serie_ID = serie_ID, ITK_image = ITK_image)

    def get_serie_length(self):
        return self.total_slices
    
    def get_image_slice(self, slice_number):
        if self.ITK_image is None:
            reader = sitk.ImageFileReader()
            reader.SetFileName(self.reader.GetFileNames()[slice_number])
            ITK_image = reader.Execute()
            ITK_image.SetDirection((1,0,0,0,1,0,0,0,1))
            ITK_image.SetOrigin((0,0,0))
            return ITK_image[:,:,0] #preventing 3D images to be passed to the viewer
        else:
            return self.ITK_image[:,:,slice_number]
    
    def get_serie_size(self):
        if self.ITK_image is None:
            size = list(self.preview_reader.GetSize())
            size[-1] = self.total_slices
        else:
            size = self.ITK_image.GetSize()
        return tuple(size)
    
    def get_serie_image(self):
        if self.ITK_image is None:
            self.ITK_image = self.reader.Execute()
            self.ITK_image.SetDirection((1,0,0,0,1,0,0,0,1))
            self.ITK_image.SetOrigin((0,0,0))
        return self.ITK_image