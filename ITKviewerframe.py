import tkinter as tk  
from tkinter import ttk, Label, Menu, filedialog
import logging
import numpy as np
from PIL import Image, ImageTk
import math
from Utils import timer_func
import SimpleITK as sitk
from reloading import reloading
from Utils import PatchedLabel

class ITKviewerFrame(tk.Frame):
    """ ITK viewer Frame """
    def __init__(self, mainframe, FrameManager = None,  **kwargs):
        """ Initialize the ITK viewer Frame """
        super().__init__(mainframe, **kwargs)
        self.mainframe = mainframe
        self.FrameManager = FrameManager
        self.zoom_delta = 1
        self.zoom = 1
        self.slice_index = 0
        self.window = 1400
        self.level = 300
        
        self.start_click_location_X = None
        self.start_click_location_Y = None

        self.center_X = 0
        self.center_Y = 0

        self.interpolate = Image.NEAREST

        self.ITK_image = self.get_dummy_SITK_image()

        self.frame = self
        self.frame.grid(row=0, column=0, sticky="news")

        self.image_label = PatchedLabel(self.frame)  
        self.image_needs_updating = True
        # https://stackoverflow.com/questions/7591294/how-to-create-a-self-resizing-grid-of-buttons-in-tkinter
        self.initialize()
        self.image_label.grid(row=0, column=0, sticky="news", padx=5, pady=5)

        self.label_meta_info = tk.Label(self.frame, text=f"Window: {self.window}, Level: {self.level}")
        self.label_meta_info.grid(row=1, column=0, sticky=tk.E + tk.W, pady=1) 
        
        self.image_needs_updating = True
        self.image = ImageTk.PhotoImage(self.get_image_from_HU_array_with_zoom())  # create image object
        self.image_label.configure(image=self.image)

        self.frame.rowconfigure(0, weight=1)
        self.frame.columnconfigure(0, weight=1)

    def initialize(self):
        """ placeholder """
        self.image_label.bind('<MouseWheel>', self.__scroll)  # zoom for Windows and MacOS, but not Linux
        self.image_label.bind('<Button-5>',   self.__scroll)  # zoom for Linux, wheel scroll down
        self.image_label.bind('<Button-4>',   self.__scroll)  # zoom for Linux, wheel scroll up
        self.image_label.bind('<Up>', lambda event: self.next_slice())
        self.image_label.bind('<Down>', lambda event: self.previous_slice())
        self.image_label.bind('<Control-MouseWheel>', self.__zoom)
        self.image_label.bind('<Right>', lambda event: self.zoom_in())
        self.image_label.bind('<Left>', lambda event: self.zoom_out())
        self.image_label.bind('<Control-B1-Motion>', self.pan_image)
        self.image_label.bind('<Shift-B1-Motion>', self.change_window_level)
        self.image_label.bind('<ButtonPress-1>', self.start_drag_event_image , add='+')
        self.image_label.bind('<ButtonRelease-1>', self.stop_drag_event_image)
        self.image_label.bind('<Motion>', self.update_label_meta_info_value)
        self.image_label.bind('<B1-Motion>', self.drag_event_rel_coord)
        # self.image_label.bind('<Configure>', lambda event: self.update_image())
        self.image_label.bind('<Leave>', self.on_leave)
        # self.frame.bind('<Configure>', lambda event: self.update_image_frame())
        self.bind('<FocusIn>', self.on_focus_in)
        # self.bind('<FocusOut>', self.on_focus_out)

    def on_focus_in(self, event):
        self.configure(bg="red")
        self.FrameManager.set_active_widget(self)

    def on_focus_out(self, event = None):
        self.configure(bg="yellow")

    def on_leave(self, event):
        self.label_meta_info.config(text=f"Window: {self.window}, Level: {self.level}")

    def get_dummy_DiCOM_array(self):
        """placeholder"""
        np_array= np.empty((512,512,50))
        number = 0
        for i in range(np_array.shape[0]):
            for j in range(np_array.shape[1]):
                np_array[i,j,:] = number
                number += 1

        return np_array

    def get_empty_image(self,x ,y):
        """ Return empty image """
        return Image.new("RGB", (x, y), (0, 0, 0))
    
    def get_dummy_SITK_image(self):
        """placeholder"""
        image = sitk.Image(512,512,50, sitk.sitkInt16)
        number = 10
        for i in range(int(image.GetSize()[0]/2)):
            image[i*2, :,:] = number
            number += 3
        image.SetSpacing([0.5,0.75,1])
        image.SetOrigin([6,0.15,0])
        image.SetDirection([1,0.25,0,0,0.75,0,0,0,1])
        return image

    @timer_func(FPS_target=50000)
    def get_image_from_HU_array(self, img_type="RGBA"):
        """ Return image from HU array """
        # https://github.com/jonasteuwen/SimpleITK-examples/blob/master/examples/apply_lut.py
        logging.debug("get_image_from_HU_array")
        minimum_hu = self.level - (self.window/2)
        maximum_hu  = self.level + (self.window/2)

        max_output_value = 255
        min_output_value = 0

        pixel_type = self.ITK_image.GetPixelIDValue()
        if (pixel_type == sitk.sitkUInt8 or pixel_type == sitk.sitkUInt16 or pixel_type == sitk.sitkUInt32 or pixel_type == sitk.sitkUInt64) and minimum_hu < 0:
            min_output_value = int( abs(minimum_hu) / (maximum_hu - minimum_hu) )
            minimum_hu = 0
        
        self.slice_gray_ITK_image = sitk.IntensityWindowing(self.ITK_image[:,:, self.slice_index],
                                            int(minimum_hu), int(maximum_hu),
                                            min_output_value,
                                            max_output_value)
        self.slice_gray_ITK_image = sitk.Cast(self.slice_gray_ITK_image, sitk.sitkUInt8)
        np_slice_gray_image = sitk.GetArrayFromImage(self.slice_gray_ITK_image)
        
        img_arr = Image.fromarray(np_slice_gray_image, "L").convert(img_type)
        return img_arr
    
    
    def get_image_from_HU_array_with_zoom(self, force_update=False):
        """placeholder"""
        
        self.get_image_from_HU_array(img_type="RGBA")
        logging.debug("zooming in")
        self.slice_ITK_image = self.slice_gray_ITK_image
        self.slice_PIL_image_trasformed = self.zoom_itk()
        self.image_needs_updating = False
        return self.slice_PIL_image_trasformed

    def update_image(self):
        """placeholder"""
        self.image = ImageTk.PhotoImage(self.get_image_from_HU_array_with_zoom())
        self.image_label.configure(image=self.image)

    def update_image_frame(self):
        """placeholder"""
        # print("update_image_frame")
        # self.update_nested_parents(self.image_label)
        # # self.frame.update()
        self.frame.rowconfigure(0, weight=1)
        self.frame.columnconfigure(0, weight=1)
        print("update_image_frame in ITK_image_viewer")
        self.update_image()

    def update_nested_parents(self, widget, parents=[]):
        """placeholder"""
        widget.update()
        parents = parents + [widget.winfo_parent()]
        if widget.winfo_parent() != ".":
            self.update_nested_parents(widget._nametowidget(widget.winfo_parent()), parents)
        else:
            for parent in parents:
                widget._nametowidget(parent).update()
    
    def load_new_CT(self, window: int = 600, level: int = 301, ITK_image: sitk.Image = None):
        """placeholder"""
        logging.debug("load_new_CT")
        if ITK_image is not None:
            self.ITK_image = ITK_image

        self.slice_index = 0
        
        self.center_X = 0
        self.center_Y = 0
        self.zoom = 1
        self.zoom_delta = 1
        if window is not None:
            self.window = window
        if level is not None:
            self.level = level

        self.image_needs_updating = True
        self.update_image()

    def __scroll(self, event):
        logging.debug("Scrolling")
        self.focus_set()
        self.image_needs_updating = True
        if event.delta == -120:  # scroll down, smaller
            self.previous_slice()
        if event.delta == 120:  # scroll up, bigger
            self.next_slice()
       
    def __zoom(self, event):
        logging.debug("zooming")
        self.focus_set()
        if event.delta == -120:
            self.zoom_out()
        if event.delta == 120:
            self.zoom_in()

    def next_slice(self):
        logging.debug("Next slice")
        self.image_needs_updating = True
        self.slice_index += 1
        CT_image_cache = None
        if self.slice_index >= self.ITK_image.GetSize()[2]:
            self.slice_index = self.ITK_image.GetSize()[2] - 1
        self.update_image()
        
    def previous_slice(self):
        self.image_needs_updating = True
        logging.debug("Previous slice")
        self.slice_index -= 1
        CT_image_cache = None
        if self.slice_index < 0:
            self.slice_index = 0
        self.update_image()
        

    def zoom_in(self):
        logging.debug("Zoom In")
        self.zoom_delta += 0.1
        self.update_zoom()
        self.update_image()

    def zoom_out(self):
        logging.debug("Zoom out")
        self.zoom_delta -= 0.1
        self.update_zoom()
        self.update_image()
    
    def update_zoom(self):
        self.zoom = 2 ** self.zoom_delta /2

    def pan_image(self, event):
        logging.debug("panning")
        self.focus_set()
        self.mainframe.update_idletasks()
        if (self.start_click_location_X == event.x or self.start_click_location_X == None) and (self.start_click_location_Y == event.y or self.start_click_location_Y == None):
            logging.error("pan invalid")
            return
        
        logging.debug("doing pan")
        delta_x, delta_y = self.drag_event_rel_coord(event)
        self.center_X += (delta_x) / self.zoom
        self.center_Y += (delta_y) / self.zoom
        logging.debug("center X: %s, center Y: %s", self.center_X, self.center_Y)

        self.update_image()

    def start_drag_event_image(self, event):
        logging.debug("start pan")
        self.focus_set()
        self.drag_mode = False
        self.start_click_location_X = event.x
        self.start_click_location_Y = event.y

    def stop_drag_event_image(self, event):
        logging.debug("stop pan")
        if (self.start_click_location_X == event.x) and (self.start_click_location_Y == event.y) and self.drag_mode == False:
            logging.debug("button 1 pressed event")
            y ,x = self.get_mouse_location_dicom(event)
            self.button1_press_event_image(x, y)
        self.drag_mode = False
        self.start_click_location_X = None
        self.start_click_location_Y = None
    
    def button1_press_event_image(self, x,y):
        pass

    
    def get_mouse_location_dicom(self, event = None, coords = None):
        w_l , w_h = self.image_label.winfo_width(), self.image_label.winfo_height()
        sp_x , sp_y = self.slice_gray_ITK_image.GetSpacing()
        if event is not None:
            x, y = self.ITK_image[:,:, self.slice_index].TransformPhysicalPointToIndex(self.transform.TransformPoint((event.x, event.y)))
        elif coords is not None:
            x, y = self.ITK_image[:,:, self.slice_index].TransformPhysicalPointToIndex(self.transform.TransformPoint((coords[0], coords[1])))
        else:
            logging.error("No event or coords passed")
            return None, None        
        return x, y

    def get_visible_DICOM_coords(self):
        w_l , w_h = self.image_label.winfo_width(), self.image_label.winfo_height()
        points = [self.get_mouse_location_dicom(coords = coords) for coords in [(0,0), (w_l, 0), (0, w_h), (w_l, w_h)]]
        return points
    
    def update_label_meta_info_value(self, event):
        x, y = self.get_mouse_location_dicom(event)
        if x < 0 or x >= self.ITK_image.GetSize()[0] or y < 0 or y >= self.ITK_image.GetSize()[1]:
            logging.debug("mouse out of bounds")
            self.label_meta_info.config(text=f"Window: {self.window}, Level: {self.level}")
            return
        HU = self.ITK_image[x,y, self.slice_index]
        self.label_meta_info.config(text=f"Window: {self.window}, Level: {self.level}, HU: {HU}")
        
    def drag_event_rel_coord(self, event):
        logging.debug("dragging")
        self.focus_set()
        self.drag_mode = True
        delta_x, delta_y = self.B1_drag_event(event)
        return delta_x, delta_y

    def B1_drag_event(self, event):
        delta_x = self.start_click_location_X - event.x
        delta_y = self.start_click_location_Y - event.y

        self.start_click_location_X = event.x
        self.start_click_location_Y = event.y
        if self.drag_mode == False:
            self.bind_drag_event(delta_x, delta_y)
        return delta_x, delta_y

    def bind_drag_event(self, delta_x, delta_y):
        return

    def change_window_level(self, event):
        logging.debug("windowing")
        self.focus_set()
        self.image_needs_updating = True
        self.mainframe.update_idletasks()
        if (self.start_click_location_X == event.x or self.start_click_location_X == None) and (self.start_click_location_Y == event.y or self.start_click_location_Y == None):
            logging.error(" windowing invalid")
            return
        logging.debug("windowing pan")
        delta_x, delta_y = self.drag_event_rel_coord(event)
        self.window += delta_x
        self.level += delta_y
        
        self.label_meta_info.config(text=f"Window: {self.window}, Level: {self.level}")

        self.update_image()
    
    def zoom_itk(self, *args, **kwargs):        
        transform = sitk.Similarity2DTransform(self.slice_ITK_image.GetDimension())
        transform.SetCenter((0,0))
        transform.SetTranslation((self.center_X, self.center_Y))
        transform.SetScale(1/ self.zoom)
        self.transform = transform
        logging.debug([self.image_label.winfo_width(), self.image_label.winfo_height()])
        size = [self.image_label.winfo_width(), self.image_label.winfo_height()]
        self.slice_ITK_image_transformed = sitk.Resample(self.slice_ITK_image, transform, sitk.sitkNearestNeighbor, size =size)
        
        if   self.slice_ITK_image_transformed.GetNumberOfComponentsPerPixel() == 1:
            return Image.fromarray( sitk.GetArrayFromImage(self.slice_ITK_image_transformed).astype(np.uint8), mode="L")
        elif self.slice_ITK_image_transformed.GetNumberOfComponentsPerPixel() == 3:
            return Image.fromarray( sitk.GetArrayFromImage(self.slice_ITK_image_transformed).astype(np.uint8), mode="RGB")
