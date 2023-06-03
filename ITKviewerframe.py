import tkinter as tk  
from tkinter import ttk, Label, Menu, filedialog
import logging
import numpy as np
from PIL import Image, ImageTk
import math

class ITKviewerFrame(tk.Frame):
    """ ITK viewer Frame """
    def __init__(self, mainframe, **kwargs):
        """ Initialize the ITK viewer Frame """
        super().__init__(mainframe, **kwargs)
        self.mainframe = mainframe

        self.image_Frame = tk.Frame(self)

        self.image_label = Label(self.image_Frame)
        self.image_label.grid(row=0, column=0, sticky=tk.N+tk.S+tk.E+tk.W)
        
        self.initialize()

        self.image = ImageTk.PhotoImage(self.get_image_from_HU_array())  # create image object


        self.mouse_location_HU = tk.Label(self.image_Frame, text=f"Window: {self.window}, Level: {self.level}")
        self.mouse_location_HU.grid(row=1, column=0, sticky=tk.E + tk.W, pady=1) 
        
        self.image_Frame.grid(row=0, column=0, sticky=tk.N+tk.S+tk.E+tk.W)
        self.image_Frame.rowconfigure(0, weight=1)
        self.image_Frame.columnconfigure(0, weight=1)



    def initialize(self):
        """ placeholder """
        self.zoom_delta = 1 
        self.zoom = 1
        self.slice_index = 1
        self.np_HU_array = np.empty((50,512,512))
        self.window = 1400
        self.level = 300

        self.center_X = self.np_HU_array.shape[1] /2
        self.center_Y = self.np_HU_array.shape[2] /2

        self.interpolate = Image.NEAREST

        self.mainframe.bind('<MouseWheel>', self.__scroll)  # zoom for Windows and MacOS, but not Linux
        self.mainframe.bind('<Button-5>',   self.__scroll)  # zoom for Linux, wheel scroll down
        self.mainframe.bind('<Button-4>',   self.__scroll)  # zoom for Linux, wheel scroll up
        self.mainframe.bind('<Up>', lambda event: self.next_slice())
        self.mainframe.bind('<Down>', lambda event: self.previous_slice())
        self.mainframe.bind('<Control-MouseWheel>', self.__zoom)
        self.mainframe.bind('<Right>', lambda event: self.zoom_in())
        self.mainframe.bind('<Left>', lambda event: self.zoom_out())
        self.mainframe.bind('<Control-B1-Motion>', self.pan_image)
        self.mainframe.bind('<Shift-B1-Motion>', self.change_window_level)
        self.mainframe.bind('<ButtonPress-1>', self.start_drag_event_image) #stop_pan_image
        self.mainframe.bind('<ButtonRelease-1>', self.stop_drag_event_image)
        self.mainframe.bind('<Motion>', self.update_mouse_location_HU_value)

    def get_empty_image(self,x ,y):
        """ Return empty image """
        return Image.new("RGB", (x, y), (0, 0, 0))

    def get_image_from_HU_array(self):
        minimum_hu = self.level - (self.window/2)
        maximum_hu  = self.level + (self.window/2)

        np_HU_2D_array = np.copy(self.np_HU_array[self.slice_index,:,:])
        np_HU_2D_array[np_HU_2D_array < minimum_hu] = minimum_hu
        np_HU_2D_array[np_HU_2D_array > maximum_hu] = maximum_hu

        with np.errstate(invalid='raise'):
            try:
                np_gray_array = np.divide(np_HU_2D_array - np_HU_2D_array.min(), 
                                    (np_HU_2D_array.max() - np_HU_2D_array.min())
                                    )*255
            except FloatingPointError:
                np_gray_array = np.zeros(np_HU_2D_array.shape)
            except Exception as e:
                logging.error(e)
        np_gray_array = np_gray_array.astype(np.uint8)

        img_arr = Image.fromarray(np_gray_array, "L").convert('RGBA')
        
        
        logging.debug("zooming in")
        img_arr = self.zoom_at(img_arr, x = self.center_X, y = self.center_Y, zoom= self.zoom_delta, interpolate= self.interpolate)


        return img_arr

    def update_image(self):
        """placeholder"""
        self.image = ImageTk.PhotoImage(self.get_image_from_HU_array())
        self.image_label.configure(image=self.image)

    def load_new_CT(self, np_HU_array: np.ndarray):
        """placeholder"""
        self.np_HU_array = np_HU_array
        
        self.center_X = self.np_HU_array.shape[1] /2
        self.center_Y = self.np_HU_array.shape[2] /2
        
        self.update_image()

    def __scroll(self, event):
        logging.debug("Scrolling")
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
        self.slice_index += 1
        CT_image_cache = None
        if self.slice_index >= self.np_HU_array.shape[0]:
            self.slice_index = self.np_HU_array.shape[0] - 1
        self.update_image()
        
    def previous_slice(self):
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
        self.center_X += (self.start_click_location_X - event.x) / self.zoom
        self.center_Y += (self.start_click_location_Y - event.y) / self.zoom
        logging.info("center X: %s, center Y: %s", self.center_X, self.center_Y)
        self.start_click_location_X = event.x
        self.start_click_location_Y = event.y

        self.update_image()

    def start_drag_event_image(self, event):
        logging.debug("start pan")
        self.start_click_location_X = event.x
        self.start_click_location_Y = event.y

    def stop_drag_event_image(self, event):
        logging.debug("stop pan")
        self.start_click_location_X = None
        self.start_click_location_Y = None
    
    def get_mouse_location_dicom(self, event):
        w_l , w_h = self.image_label.winfo_width(), self.image_label.winfo_height()
        x = math.floor(self.center_X + (event.x - w_l/2) / self.zoom)
        y = math.floor(self.center_Y + (event.y - w_h/2) / self.zoom)
        return x, y

    def update_mouse_location_HU_value(self, event):
        x, y = self.get_mouse_location_dicom(event)
        if x < 0 or x >= self.np_HU_array.shape[2] or y < 0 or y >= self.np_HU_array.shape[1]:
            logging.debug("mouse out of bounds")
            self.mouse_location_HU.config(text=f"Window: {self.window}, Level: {self.level}")
            return
        HU = self.np_HU_array[self.slice_index, y, x]
        self.mouse_location_HU.config(text=f"Window: {self.window}, Level: {self.level}, HU: {HU}")
        

    def change_window_level(self, event):
        self.mainframe.update_idletasks()
        if (self.start_click_location_X == event.x or self.start_click_location_X == None) and (self.start_click_location_Y == event.y or self.start_click_location_Y == None):
            logging.error(" windowing invalid")
            return
        logging.debug("windowing pan")
        self.window += self.start_click_location_X - event.x
        self.level += self.start_click_location_Y - event.y

        self.start_click_location_X = event.x
        self.start_click_location_Y = event.y

        self.mouse_location_HU.config(text=f"Window: {self.window}, Level: {self.level}")

        self.update_image()

    def zoom_at(self, img, x = 0, y = 0, zoom = 1, interpolate = Image.LANCZOS):
        """ Zoom at x,y location"""
        zoom = 2 ** zoom / 2
        w_l , w_h = self.image_label.winfo_width(), self.image_label.winfo_height()
        bg = self.get_empty_image(w_l, w_h)
        
        fg = img.resize((int(img.width * self.zoom), int(img.height * self.zoom)), interpolate)
        w, h = fg.size
        bg.paste(fg, (int(w_l / 2 - x * self.zoom), int(w_h / 2 - y * self.zoom)))
        return bg
