import re
import logging 
from tkinter import ttk, Label
import numpy as np
import tkinter as tk 
import SimpleITK as sitk
from PIL import ImageTk
from ..Utils import PatchedFrame
import PIL.Image
import PIL.ImageDraw

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

class DICOM_serie_instance(PatchedFrame):
    """placeholder"""
    def __init__(self, mainframe, serie_ID, **kwargs):
        super().__init__(mainframe, **kwargs)
        self.mainframe = mainframe
        self.serie_ID = serie_ID
        self.ITK_image = None # preserving RAM if entire serie is not needed

        self.total_slices = None
        self.preview_image = None

        self.preview_label = Label(self, width=150, height=150)
        self.preview_label.grid(row=0, column=0, sticky='w')

        self.set_preview_image(None)
        
        self.config(width=125)

        self.button = ttk.Button(self, text=self.serie_ID)
        self.button.grid(row=1, column=0)

        self.make_draggable()

    def set_preview_image(self, image):
        if image is None:
            image = PIL.Image.new("RGB", (512,512), (255,255,255))
            draw = PIL.ImageDraw.Draw(image)
            draw.text((10,10), "No image loaded", fill="black")
        self.preview_image = ImageTk.PhotoImage(image)
        self.preview_label.config(image=self.preview_image)
        self.preview_label.image = self.preview_image



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
    
    def load_serie(self) -> sitk.Image:
        """ Load the serie into memory as a SimpleITK image """
        logging.warning(f"Not implemented: {self.__class__.__name__}.load_serie")

    def unload_serie(self):
        """ Unload the serie from memory """
        self.ITK_image = None

    def get_serie_size(self) -> tuple:
        """" Get the size of the serie """
        if self.ITK_image is None:
            logging.warning(f"serie {self.serie_ID} is not loaded")
            self.load_serie()
            return tuple(self.ITK_image.GetSize) if self.ITK_image is not None else None
        return tuple(self.ITK_image.GetSize())
    
    def get_serie_image(self) -> sitk.Image:
        """ Get the SimpleITK image of the serie """
        logging.warning(f"Not implemented: {self.__class__.__name__}.get_serie_image")