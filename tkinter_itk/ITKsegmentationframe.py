from PIL import Image, ImageTk
import tkinter as tk
import SimpleITK as sitk
import numpy as np
import logging
from .Utils import PatchedFrame
from .ITKviewerframe import ITKviewerFrame
from .segmentation_serie_manager import Segmentation_serie_manager
import time

def set_mask_value(image, mask, value):
    msk32 = sitk.Cast(mask, sitk.sitkFloat32)
    msk32.CopyInformation(image)
    return sitk.Cast(sitk.Cast(image, sitk.sitkFloat32) *
                     sitk.InvertIntensity(msk32, maximum=1.0) + 
                     msk32*value, image.GetPixelID())

class SearchableComboBox(PatchedFrame):
    def __init__(self, options, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.dropdown_id = None
        self.options = options
        self.timeout = 2000 # 2 seconds
        self.time_last_activity = 0

        # Create a Text widget for the entry field
        # wrapper = tk.Frame(root)
        # wrapper.grid(row=0, column=0)

        self.entry = tk.Entry(self, width=24)
        self.entry.bind("<KeyRelease>", self.on_entry_key)
        self.entry.bind("<FocusIn>", self.show_dropdown) 
        self.entry.bind("<Return>", lambda event: self.add_option(self.entry.get(), show_dropdown=True))
        self.entry.bind("<FocusOut>", lambda event: self.hide_dropdown(force=True))
        self.entry.bind("<Button-1>", self.show_dropdown)
        self.entry.bind("<Escape>", lambda event: self.hide_dropdown(force=True))
        self.entry.grid(row=0, column=0, sticky="ew")

        # Dropdown icon/button
        tk.Button(self, command=self.show_dropdown).grid(row=0, column=1, sticky="ew")

        # Create a Listbox widget for the dropdown menu
        self.listbox = tk.Listbox(self.master, height=5, width=30)
        self.listbox.bind("<<ListboxSelect>>", self.on_select)
        self.listbox.bind("<Double-Button-1>", lambda event: self.on_select(event, hide_dropdown=True))
        self.listbox.bind("<Motion>", self.event_activity)
        for option in self.options:
            self.listbox.insert(tk.END, option)

    def on_entry_key(self, event):
            self.time_last_activity = time.time()
            typed_value = event.widget.get().strip().lower()
            if not typed_value:
                # If the entry is empty, display all options
                self.listbox.delete(0, tk.END)
                for option in self.options:
                    self.listbox.insert(tk.END, option)
            else:
                # Filter options based on the typed value
                self.listbox.delete(0, tk.END)
                filtered_options = [option for option in self.options if option.lower().startswith(typed_value)]
                for option in filtered_options:
                    self.listbox.insert(tk.END, option)
            self.show_dropdown()

    def on_select(self, event, hide_dropdown=False):
            self.time_last_activity = time.time()
            selected_index = self.listbox.curselection()
            if selected_index:
                selected_option = self.listbox.get(selected_index)
                self.entry.delete(0, tk.END)
                self.entry.insert(0, selected_option)
                if hide_dropdown:
                    self.hide_dropdown(force=True)
            self.event_generate("<<OptionSelected>>")
    def show_dropdown(self, event=None):
            self.time_last_activity = time.time()
            self.reset_dropdown_filter() # Reset filter to show all options on popup
            self.listbox.place(in_=self.entry, x=0, y = -self.listbox.winfo_reqheight())
            self.listbox.lift()

            # Show dropdown for 2 seconds
            if self.dropdown_id: # Cancel any old events
                self.listbox.after_cancel(self.dropdown_id)
            self.dropdown_id = self.listbox.after(self.timeout, self.hide_dropdown)

    def add_option(self, option, show_dropdown=False):
        self.time_last_activity = time.time()
        if option == "":
            return
        if option not in self.options:
            self.options.append(option)
            self.update_dropdown()
            if show_dropdown:
               self.show_dropdown()

    def update_dropdown(self):
        self.time_last_activity = time.time()
        typed_value = self.entry.get().strip().lower()
        self.listbox.delete(0, tk.END)
        for option in self.options:
            if option.lower().startswith(typed_value):
                self.listbox.insert(tk.END, option)

    def update_options(self, options):
        self.time_last_activity = time.time()
        self.options = options
        self.update_dropdown()

    def event_activity(self, event):
        self.time_last_activity = time.time()

    def hide_dropdown(self, force=False):
        if force:
            self.time_last_activity = 0
            self.listbox.place_forget()
            self.event_generate("<<OptionSelected>>")
            return
        ms_since_last_activity = (time.time() - self.time_last_activity) * 1000
        # print(f"Time since last activity: {ms_since_last_activity}")
        if ms_since_last_activity > self.timeout:
            # print("Hiding dropdown")
            self.time_last_activity = 0
            self.listbox.place_forget()
            self.event_generate("<<OptionSelected>>")
        else:
            # print(self.timeout - ms_since_last_activity)
            self.listbox.after(int(self.timeout - ms_since_last_activity), self.hide_dropdown)

    def set_option(self, option):
        if option not in self.options:
            self.options.append(option)
            self.update_dropdown()
        
        if option == "":
            return
        if self.entry.get() == option:
            return
            
        self.entry.delete(0, tk.END)
        self.entry.insert(0, option)
        self.event_generate("<<OptionSelected>>")

    def get_option(self):
        return self.entry.get()

    def reset_dropdown_filter(self):
        self.listbox.delete(0, tk.END)
        for option in self.options:
            self.listbox.insert(tk.END, option)
        


class ITKsegmentationFrame(ITKviewerFrame):
    def __init__(self, parent, **kwargs):
        """ Initialize the ITK viewer Frame """
        self.max_layers = 255
        self.opacity = 0.5
        self.seg_image_needs_update = True

        super().__init__(parent, **kwargs)
        self.parent = parent
        self.seg_image = ImageTk.PhotoImage(self.get_image_from_seg_array())

        self.segmentation_selection.grid(row=2, column=0, sticky="ew")
        self.segmentation_selection.bind("<<OptionSelected>>", self.seg_name_changed)

    def initialize(self):
        self.segmentation_serie_manager: Segmentation_serie_manager = self.FrameManager.parent.segmentation_serie_manager
        self.segmentation_selection = SearchableComboBox(["default"], self)
        self.segmentation_selection.set_option("default")

        if self.serie_ID is None:
            self.ITK_seg_image = None
        else:
            self.ITK_seg_image = self.segmentation_serie_manager.get_image(self.serie_ID, add_if_not_exist=True)
        
        super().initialize()
    
    def load_new_CT(self, window: int = None, level: int = None, ITK_image: sitk.Image = None,**kwargs):
        """placeholder"""
        super().load_new_CT(window, level, ITK_image= ITK_image, update_image = False, **kwargs)
        self.segmentation_selection.set_option("default")
        self.segmentation_selection.update_options(self.segmentation_serie_manager.get_segmentation_names(self.serie_ID))
        self.seg_image_needs_update = True
        if self.serie_ID is None:
            self.ITK_seg_image = sitk.Image(ITK_image.GetSize(), sitk.sitkUInt8)
            self.ITK_seg_image.CopyInformation(ITK_image)
        else:
            self.ITK_seg_image = self.segmentation_serie_manager.get_image(self.serie_ID, add_if_not_exist=True)
        self.update_image()
    
    def get_image_from_seg_array(self):
        """placeholder"""
        if self.ITK_seg_image is None:
            return Image.new("RGB", (512,512), (255,255,255))
        else:
            image_segmentation_array = sitk.GetArrayFromImage(sitk.LabelToRGB(self.ITK_seg_image[:,:, self.slice_index]))

        return Image.fromarray(image_segmentation_array, "RGB")

    
    def zoom_itk(self, *args, **kwargs):
        """ Zoom at x,y location"""
        
        # loading the preview image if it exists
        if self.segmentation_serie_manager.has_preview(self.serie_ID):
            self.ITK_seg_image = self.segmentation_serie_manager.get_preview(self.serie_ID)
        else:
            self.ITK_seg_image = self.segmentation_serie_manager.get_image(self.serie_ID, name = self.seg_name, add_if_not_exist=True)
                                       
        NP_seg_slice = self.ITK_seg_image[:,:, self.slice_index]
        if NP_seg_slice.GetSize() != self.slice_gray_ITK_image.GetSize():
            logging.warning("Segmentation image size does not match image size")
            self.ITK_seg_image = sitk.Image(self.slice_gray_ITK_image.GetSize(), sitk.sitkUInt8)
            self.ITK_seg_image.CopyInformation(self.slice_gray_ITK_image)
            return
        NP_seg_slice.CopyInformation(self.slice_gray_ITK_image)

        pixel_type = self.slice_gray_ITK_image.GetPixelID()
        if pixel_type != sitk.sitkVectorUInt8 and pixel_type != sitk.sitkVectorUInt16 and pixel_type != sitk.sitkVectorUInt32 and pixel_type != sitk.sitkVectorUInt64:
            self.slice_ITK_image = sitk.LabelOverlay(self.slice_gray_ITK_image, NP_seg_slice, opacity=self.opacity)
        return super().zoom_itk(*args, **kwargs)        


    def set_segmentation_point_current_slice(self, x, y, layer_height):
        self.ITK_seg_image[x, y, self.slice_index] = layer_height
        self.seg_image_needs_update = True
        self.update_image()

    def set_segmentation_mask_current_slice(self, layer_height: int, mask: np.ndarray):
        
        self.ITK_seg_image[:, :, self.slice_index] = set_mask_value(self.ITK_seg_image[:, :, self.slice_index], mask, layer_height) 
        self.seg_image_needs_update = True
        self.update_image()
    
    def set_segmentation_preview_mask_current_slice(self, layer_height: int, mask: np.ndarray):
        preview_image = self.segmentation_serie_manager.get_segmentation(self.serie_ID, add_if_not_exist=True, name=self.seg_name).__copy__()
        preview_image[:, :, self.slice_index] = set_mask_value(preview_image[:, :, self.slice_index], mask, layer_height)
        self.segmentation_serie_manager.set_preview(self.serie_ID, preview_image)
        self.seg_image_needs_update = True
        self.update_image()

    def clear_segmentation_mask_current_slice(self, layer_height: int = None):
        if layer_height is None:
            self.ITK_seg_image[:, :, self.slice_index] = 0
        else:
            self.ITK_seg_image[:, :, self.slice_index] = set_mask_value(self.ITK_seg_image[:, :, self.slice_index], self.ITK_seg_image[:, :, self.slice_index] == layer_height, 0)
        self.seg_image_needs_update = True
        self.update_image()

    def next_slice(self):
        self.seg_image_needs_update = True
        return super().next_slice()
    
    def previous_slice(self):
        self.seg_image_needs_update = True
        return super().previous_slice()

    def get_NP_seg_slice(self):
        return sitk.GetArrayFromImage(self.ITK_seg_image[:,:, self.slice_index])
    
    def set_NP_seg_slice(self, NP_seg_slice: np.ndarray):
        if self.ITK_seg_image.GetPixelIDValue() == sitk.sitkUInt8:
            if NP_seg_slice.max() > 255:
                logging.error("Segmentation image has values above 255, converting to uint8")
                NP_seg_slice = NP_seg_slice.astype(np.uint8)
            NP_seg_slice = NP_seg_slice.astype(np.uint8)
        elif self.ITK_seg_image.GetPixelIDValue() == sitk.sitkUInt16:
            if NP_seg_slice.max() > 65535:
                logging.error("Segmentation image has values above 65535, converting to uint16")
                NP_seg_slice = NP_seg_slice.astype(np.uint16)
            NP_seg_slice = NP_seg_slice.astype(np.uint16)
        elif self.ITK_seg_image.GetPixelIDValue() == sitk.sitkUInt32:
            if NP_seg_slice.max() > 4294967295:
                logging.error("Segmentation image has values above 4294967295, converting to uint32")
            NP_seg_slice = NP_seg_slice.astype(np.uint32)
        elif self.ITK_seg_image.GetPixelIDValue() == sitk.sitkUInt64:
            if NP_seg_slice.max() > 18446744073709551615: # would be very impressive if you have a segmentation image with values above this
                logging.error("Segmentation image has values above 18446744073709551615, converting to uint64")
            NP_seg_slice = NP_seg_slice.astype(np.uint64)
        self.ITK_seg_image[:,:, self.slice_index] = sitk.GetImageFromArray(NP_seg_slice)
        self.seg_image_needs_update = True
        self.update_image()

    def accept_preview(self):
        self.segmentation_serie_manager.accept_preview(self.serie_ID, name=self.seg_name)
        self.update_image()

    def update_image(self):
        if self.segmentation_serie_manager.has_preview(self.serie_ID):
            self.configure(bg = "green")
        if self.segmentation_selection.options != self.segmentation_serie_manager.get_segmentation_names(self.serie_ID):
            self.segmentation_selection.update_options(self.segmentation_serie_manager.get_segmentation_names(self.serie_ID))
        return super().update_image()

    def update_label_meta_info_value(self, event):
        x, y = self.get_mouse_location_dicom(event)

        if x is None or y is None:
            logging.debug("mouse out of bounds or not ITK image")
            return
        if x < 0 or x >= self.ITK_image.GetSize()[0] or y < 0 or y >= self.ITK_image.GetSize()[1] or not self.is_mouse_on_image(event):
            logging.debug("mouse out of bounds")
            self.update_label_meta_info()
            return
            
        HU = self.ITK_image[x,y, self.slice_index]
        label = self.ITK_seg_image[x,y, self.slice_index]
        # if image is not a vector image
        if self.ITK_image.GetNumberOfComponentsPerPixel() == 1:
            # self.label_meta_info.config(text=f"Window: {self.window}, Level: {self.level}, Slice: {self.slice_index}, HU: {HU:0>4}, x: {x:0>3}, y: {y:0>3}")
            # HU = f"{HU:0>4}"
            # label = f"{label:0>3}"
            self.update_label_meta_info(HU = HU, Label = label, Name = self.seg_name,  X = x, Y = y)
        else:
            # self.label_meta_info.config(text=f"Window: {self.window}, Level: {self.level}, Slice: {self.slice_index}, HU: {HU}, x: {x:0>3}, y: {y:0>3}")
            self.update_label_meta_info(HU = HU, X = x, Y = y)

    @property
    def seg_name(self):
        if not hasattr(self, "segmentation_selection"):
            return "default"
        # logging.info(f"Segmentation name: {self.segmentation_selection.get_option()}")
        return str(self.segmentation_selection.get_option())
    
    def seg_name_changed(self, event):
        # logging.info("Segmentation name changed")
        # logging.info(f"New segmentation name: {self.segmentation_selection.get_option()}")
        self.update_image()