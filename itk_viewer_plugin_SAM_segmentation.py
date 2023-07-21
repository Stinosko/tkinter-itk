import tkinter as tk  
from tkinter import ttk, Label, Menu, filedialog
import logging
import numpy as np
from Utils import Spinbox
from segment_anything import SamPredictor, sam_model_registry
from segment_anything.utils.transforms import ResizeLongestSide
import os
import torch
import SimpleITK as sitk

class SAM_segmentation:
    model_type= "vit_b"
    checkpoint = "sam_vit_b_01ec64.pth"
    device = 'cuda:0'

    name_short = "SAM"
    name_long = "SAM segmentation"

    def __init__(self, parent, **kwargs):
        self.parent = parent
        
    def load_plugin(self):
        self.parent.segmentation_modes.append(self.__class__.__name__)

    def __str__(self) -> str:
        return "ITK viewer plugin manual segmentation"
    def get_segmentation_options(self, parent):
        self.layer_height = 1
        self.sam_model = sam_model_registry[self.model_type](checkpoint=os.path.join("models", self.checkpoint))
        
        if torch.cuda.is_available():
            self.sam_model.to(device = self.device) 
        self.sam_predictor = SamPredictor(self.sam_model)        
        self.__previous_state = 0
        
        self.frame = tk.Frame(parent)
        self.frame.grid(row=0, column=1, sticky=tk.E + tk.W, pady=1)

        self.layer_frame = tk.Frame(self.frame)
        self.layer_label = tk.Label(self.layer_frame, text="Layer")
        self.layer_label.grid(row=0, column=0, sticky=tk.E + tk.W, pady=1)
        self.layer_entry = Spinbox(self.layer_frame, from_=1, to=self.parent.ITKviewer.active_widget.max_layers, width=1, command=self.update_layer)
        self.layer_entry.grid(row=1, column=0, sticky=tk.E + tk.W, pady=1)
        self.layer_entry.bind('<Return>', lambda event: self.update_layer())
        self.layer_frame.grid(row=0, column=0, sticky=tk.E + tk.W, pady=1)

        self.button = tk.Button(self.frame, text="Clear segmentation", command=self.clear_segmentation)
        self.button.grid(row=0, column=1, sticky=tk.E + tk.W, pady=1)

        self.button2 = tk.Button(self.frame, text="SAM", command=self.sam_segmentation)
        self.button2.grid(row=0, column=2, sticky=tk.E + tk.W, pady=1)

        self.button3 = tk.Button(self.frame, text="Add SAM point", command=self.toggle_add, relief = tk.RAISED)
        self.button3.grid(row=0, column=3, sticky=tk.E + tk.W, pady=1)

        self.button4 = tk.Button(self.frame, text="Remove SAM point", command=self.toggle_remove, relief = tk.RAISED)
        self.button4.grid(row=0, column=4, sticky=tk.E + tk.W, pady=1)

        self.button5 = tk.Button(self.frame, text="Reset points", command=self.reset_points)
        self.button5.grid(row=0, column=5, sticky=tk.E + tk.W, pady=1)

        self.bind1 = self.parent.ITKviewer.active_widget.image_label.bind('<ButtonPress-1>', self.button1_press_event_image, add = "+")
        self.bind2 = self.parent.ITKviewer.active_widget.image_label.bind('<ButtonPress-3>', self.button3_press_event_image, add = "+")
        self.frame.bind("<Destroy>", self.destroy)


        return self.frame

    def reset_points(self):
        self.parent.ITKviewer.active_widget.clear_segmentation_mask_current_slice(255)
        self.parent.ITKviewer.active_widget.clear_segmentation_mask_current_slice(254)
        self.stop_add()
        self.stop_remove()
        self.update_segmentation()

    def toggle_remove(self):
        if self.button4.config('relief')[-1] == 'sunken':
            self.stop_remove()
        else:
            self.stop_add()
            self.start_remove()
    
    def stop_remove(self):
        self.button4.config(relief="raised")
        self.layer_height = int(self.layer_entry.get())
        self.remove = False
    
    def start_remove(self):
        self.button4.config(relief="sunken")
        self.layer_height = int(254)
        self.remove = True

    def toggle_add(self):
        if self.button3.config('relief')[-1] == 'sunken':
            self.stop_add()
        else:
            self.stop_remove()
            self.start_add()

    def stop_add(self):
        self.button3.config(relief="raised")
        self.layer_height = int(self.layer_entry.get())
        self.add = False

    def start_add(self):
        self.button3.config(relief="sunken")
        self.layer_height = int(255)
        self.add = True

    def clear_segmentation(self):
        self.parent.ITKviewer.active_widget.clear_segmentation_mask_current_slice(self.layer_height)
        self.update_segmentation()

    def update_layer(self):
        self.layer_height = int(self.layer_entry.get())
        logging.info("update layer to %s", self.layer_height)
        self.stop_add()
        self.parent.focus_set()
        

    def mouse_in_itksegmentationframe(self, event):
        #get monitor cooridnates of mouse
        x_monitor = self.parent.mainframe.winfo_pointerx()
        y_monitor = self.parent.mainframe.winfo_pointery()
        #winfo_containing requires coordinates of the the monitor screen not relative to the main window
        if "itksegmentationframe" in self.parent.mainframe.winfo_containing(x_monitor,y_monitor).winfo_parent():
            return True
        else:
            return False

    def ctrl_is_pressed(self, event):
        if event.state - self.__previous_state == 4:  # means that the Control key is pressed
            logging.debug("ctrl_is_pressed")
            return True
        else:
            return False

    def shift_is_pressed(self, event):
        if event.state - self.__previous_state == 1:
            logging.debug("shift_is_pressed")
            return True
        else:
            return False

    def ctrl_shift_is_pressed(self, event):
        if event.state - self.__previous_state == 5:
            logging.debug("ctrl_shift_is_pressed")
            return True
        else:
            return False

    def button1_press_event_image(self, event):
        logging.info("button1_press_event_image in manual segmentation")
        #get monitor cooridnates of mouse
        if self.mouse_in_itksegmentationframe(event) == False or self.ctrl_is_pressed(event) or self.shift_is_pressed(event) or self.ctrl_shift_is_pressed(event):
            logging.debug("mouse not in itksegmentationframe")
            return
        logging.debug(event.state - self.__previous_state)
        self.__previous_state = event.state  # remember the last keystroke state
        print(self.layer_height)
        x, y = self.parent.ITKviewer.active_widget.get_mouse_location_dicom(event)
        print(x, y)
        self.parent.ITKviewer.active_widget.set_segmentation_point_current_slice(int(x), int(y), self.layer_height)
        self.update_segmentation()

    def button3_press_event_image(self, event):
        logging.info("button3_press_event_image in manual segmentation")
        #get monitor cooridnates of mouse
        if self.mouse_in_itksegmentationframe(event) == False or self.ctrl_is_pressed(event) or self.shift_is_pressed(event) or self.ctrl_shift_is_pressed(event):
            logging.debug("mouse not in itksegmentationframe")
            return
        logging.debug(event.state - self.__previous_state)
        self.__previous_state = event.state

        x, y = self.parent.ITKviewer.active_widget.get_mouse_location_dicom(event)
        self.parent.ITKviewer.active_widget.set_segmentation_point_current_slice(int(x), int(y), 0)
        self.update_segmentation()

    def update_segmentation(self):
        self.parent.ITKviewer.active_widget.update_image()
    
    def sam_segmentation(self):
        #https://github.com/facebookresearch/segment-anything/blob/main/notebooks/predictor_example.ipynb

        image = self.parent.ITKviewer.active_widget.get_image_from_HU_array(img_type = "RGB")
        self.sam_predictor.set_image(np.array(image))
        points_coords = np.empty((0, 2))
        points_labels = np.empty((0,)) # 1 is add to segmentation, 0 is remove from segmentation
        
        NP_segmentation = self.parent.ITKviewer.active_widget.get_NP_seg_slice()
        add_point = np.where(NP_segmentation == 255)
        
        for x,y in zip(add_point[1], add_point[0]):
            points_coords = np.append(points_coords, [[x, y]], axis=0)
            points_labels = np.append(points_labels, [1], axis=0)
        remove_point = np.where(NP_segmentation == 254)
        
        for x,y in zip(remove_point[1], remove_point[0]):
            points_coords = np.append(points_coords, [[x, y]], axis=0)
            points_labels = np.append(points_labels, [0], axis=0)

        self.stop_add()
        self.stop_remove()
        self.reset_points()

        masks, scores, logits = self.sam_predictor.predict(point_coords=points_coords,
                            point_labels=points_labels, 
                            multimask_output=True)
        
        mask = masks[np.argmax(scores),:,:]
        mask = sitk.GetImageFromArray(mask.astype(int))

        self.parent.ITKviewer.active_widget.set_segmentation_mask_current_slice(self.layer_height, mask)
        self.update_segmentation()

    def destroy(self, event=None):
        self.parent.ITKviewer.active_widget.clear_segmentation_mask_current_slice(255)
        self.parent.ITKviewer.active_widget.clear_segmentation_mask_current_slice(254)
        print("destroy sam segmentation")
        self.parent.ITKviewer.active_widget.image_label.unbind('<ButtonPress-1>', self.bind1)
        self.parent.ITKviewer.active_widget.image_label.unbind('<ButtonPress-3>', self.bind2)
        


main_class=SAM_segmentation