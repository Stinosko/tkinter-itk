import tkinter as tk  
from tkinter import ttk, Label, Menu, filedialog
import logging
import numpy as np
from PIL import Image, ImageTk
import math
from Utils import timer_func
import SimpleITK as sitk

class ITKviewerFrame(tk.Frame):
    """ ITK viewer Frame """
    def __init__(self, mainframe, **kwargs):
        """ Initialize the ITK viewer Frame """
        super().__init__(mainframe, **kwargs)
        self.mainframe = mainframe
        self.ITK_image = self.get_dummy_SITK_image()
        self.np_DICOM_array = sitk.GetArrayFromImage(self.ITK_image)

        self.frame = tk.Frame(self)
        self.image_label = Label(self.frame)  
              
        self.initialize()
        self.image_label.grid(row=0, column=0, sticky=tk.N+tk.S+tk.E+tk.W)
        

        self.image_needs_updating = True
        self.image = ImageTk.PhotoImage(self.get_image_from_HU_array_with_zoom())  # create image object
        self.image_label.configure(image=self.image)

        self.label_meta_info = tk.Label(self.frame, text=f"Window: {self.window}, Level: {self.level}")
        self.label_meta_info.grid(row=1, column=0, sticky=tk.E + tk.W, pady=1) 
        
        self.frame.grid(row=0, column=0, sticky=tk.N+tk.S+tk.E+tk.W)
        self.frame.rowconfigure(0, weight=1)
        self.frame.columnconfigure(0, weight=1)



    def initialize(self):
        """ placeholder """
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
        self.image_label.bind('<ButtonPress-1>', self.start_drag_event_image)
        self.image_label.bind('<ButtonRelease-1>', self.stop_drag_event_image)
        self.image_label.bind('<Motion>', self.update_label_meta_info_value)
        self.image_label.bind('<B1-Motion>', self.drag_event_rel_coord)
        self.image_label.bind('<Configure>', lambda event: self.update_image())

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
        return image

    @timer_func(FPS_target=50000)
    def get_image_from_HU_array(self, img_type="RGBA"):
        minimum_hu = self.level - (self.window/2)
        maximum_hu  = self.level + (self.window/2)
        print(minimum_hu, maximum_hu)
        self.slice_gray_image = sitk.IntensityWindowing(self.ITK_image[:,:, self.slice_index],
                                            int(minimum_hu), int(maximum_hu),
                                            0,
                                            255)
        self.slice_gray_image = sitk.Cast(self.slice_gray_image, sitk.sitkUInt8)
        np_slice_gray_image = sitk.GetArrayFromImage(self.slice_gray_image)
        
        img_arr = Image.fromarray(np_slice_gray_image, "L").convert(img_type)
        return img_arr
    
    
    def get_image_from_HU_array_with_zoom(self, force_update=False):
        """placeholder"""
        if self.image_needs_updating or force_update:
            self.base_img = self.get_image_from_HU_array(img_type="RGBA")
            logging.debug("zooming in")
        self.base_img_zoomed = self.zoom_itk(self.base_img, x = self.center_X, y = self.center_Y, zoom= self.zoom_delta, interpolate= self.interpolate)
        self.image_needs_updating = False
        return self.base_img_zoomed

    def update_image(self):
        """placeholder"""
        self.image = ImageTk.PhotoImage(self.get_image_from_HU_array_with_zoom())
        self.image_label.configure(image=self.image)

    def load_new_CT(self, np_DICOM_array: np.ndarray, window: int = 1000, level: int = 500, ITK_image: sitk.Image = None):
        """placeholder"""
        # https://github.com/jonasteuwen/SimpleITK-examples/blob/master/examples/apply_lut.py
        # center = 500
        # width = 1000

        # lower_bound = center - (width - 1)/2
        # upper_bound = center + (width - 1)/2

        # min_max = sitk.MinimumMaximumImageFilter()
        # min_max.Execute(ct_head)

        # image = sitk.IntensityWindowing(ct_head,
        #                                 lower_bound, upper_bound,
        #                                 0,
        #                                 255)
        if ITK_image is not None:
            self.ITK_image = ITK_image

        self.slice_index = 0
        self.np_DICOM_array = np_DICOM_array
        
        self.center_X = self.np_DICOM_array.shape[1] /2
        self.center_Y = self.np_DICOM_array.shape[2] /2

        if window is not None:
            self.window = window
        if level is not None:
            self.level = level

        self.image_needs_updating = True
        self.update_image()

    def __scroll(self, event):
        logging.debug("Scrolling")
        self.image_needs_updating = True
        if event.delta == -120:  # scroll down, smaller
            self.previous_slice()
        if event.delta == 120:  # scroll up, bigger
            self.next_slice()
       
    def __zoom(self, event):
        logging.debug("zooming")
        if event.delta == -120:
            self.zoom_out()
        if event.delta == 120:
            self.zoom_in()

    def next_slice(self):
        logging.debug("Next slice")
        self.image_needs_updating = True
        self.slice_index += 1
        CT_image_cache = None
        if self.slice_index >= self.np_DICOM_array.shape[0]:
            self.slice_index = self.np_DICOM_array.shape[0] - 1
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
        " "
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

    def get_mouse_location_dicom(self, event):
        w_l , w_h = self.image_label.winfo_width(), self.image_label.winfo_height()
        print()
        x = round(self.center_X + event.x / self.zoom)
        y = round(self.center_Y + event.y / self.zoom)
        return x, y

    def update_label_meta_info_value(self, event):
        x, y = self.get_mouse_location_dicom(event)
        if x < 0 or x >= self.np_DICOM_array.shape[2] or y < 0 or y >= self.np_DICOM_array.shape[1]:
            logging.debug("mouse out of bounds")
            self.label_meta_info.config(text=f"Window: {self.window}, Level: {self.level}")
            return
        HU = self.np_DICOM_array[self.slice_index, y, x]
        self.label_meta_info.config(text=f"Window: {self.window}, Level: {self.level}, HU: {HU}")
        
    def drag_event_rel_coord(self, event):
        logging.debug("dragging")
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

    def zoom_at(self, img, x = 0, y = 0, zoom = 1, interpolate = Image.LANCZOS):
        """ Zoom at x,y location"""
        zoom = 2 ** zoom / 2
        w_l , w_h = self.image_label.winfo_width(), self.image_label.winfo_height()
        bg = self.get_empty_image(w_l, w_h)
        
        fg = img.resize((int(img.width * self.zoom), int(img.height * self.zoom)), interpolate)
        bg.paste(fg, (int(w_l / 2 - x * self.zoom), int(w_h / 2 - y * self.zoom)))
        return bg

    def zoom_itk(self, *args, **kwargs):
        """ Zoom at x,y location"""
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
            self.slice_gray_image,
            output_size,
            euler2d,
            sitk.sitkNearestNeighbor,
            output_origin,
            output_spacing,
            output_direction,
        )
        return Image.fromarray( sitk.GetArrayFromImage(resampled_image).astype(np.uint8), mode="L")
        