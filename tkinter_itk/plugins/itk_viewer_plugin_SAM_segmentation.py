import tkinter as tk  
import logging
import numpy as np
from ..Utils import Spinbox
from segment_anything import SamPredictor, sam_model_registry
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
        return "ITK viewer plugin SAM segmentation"
    
    def load_segmentation_model(self):
        self.sam_model = sam_model_registry[self.model_type](checkpoint=os.path.join(os.getcwd(), "models", self.checkpoint))
        
        if torch.cuda.is_available():
            self.sam_model.to(device = self.device) 
        self.sam_predictor = SamPredictor(self.sam_model)

    def get_segmentation_options(self, parent):
        self.layer_height = 1
        self.load_segmentation_model()

        self.__previous_state = 0
        self.auto_sam = False
        self.previous_mask = None

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

        self.button2 = tk.Button(self.frame, text="Perform SAM", command=self.sam_segmentation)
        self.button2.grid(row=0, column=2, sticky=tk.E + tk.W, pady=1)

        self.button3 = tk.Button(self.frame, text="Include SAM point", command=self.toggle_add, relief = tk.RAISED)
        self.button3.grid(row=0, column=3, sticky=tk.E + tk.W, pady=1)

        self.button4 = tk.Button(self.frame, text="Exclude SAM point", command=self.toggle_remove, relief = tk.RAISED)
        self.button4.grid(row=0, column=4, sticky=tk.E + tk.W, pady=1)

        self.button5 = tk.Button(self.frame, text="Reset SAM points", command=self.reset_points)
        self.button5.grid(row=0, column=5, sticky=tk.E + tk.W, pady=1)

        self.button6 = tk.Button(self.frame, text="Enable Auto SAM", command=self.enable_auto_sam)
        self.button6.grid(row=0, column=6, sticky=tk.E + tk.W, pady=1)

        self.button7 = tk.Button(self.frame, text="Accept SAM", command=self.accept_segmentation)
        self.button7.grid(row=0, column=7, sticky=tk.E + tk.W, pady=1)

        self.bind1 = self.parent.ITKviewer.active_widget.image_label.bind('<ButtonPress-1>', self.button1_press_event_image, add = "+")
        self.bind2 = self.parent.ITKviewer.active_widget.image_label.bind('<ButtonPress-3>', self.button3_press_event_image, add = "+")
        self.bind3 = self.parent.ITKviewer.active_widget.image_label.bind('<Motion>', self.motion_event_image, add = "+")
        self.frame.bind("<Destroy>", self.destroy)

        self.include_points = []
        self.exclude_points = []

        return self.frame

    def reset_points(self):
        for point in self.include_points:
            self.parent.ITKviewer.active_widget.delete_annotation(point)
        for point in self.exclude_points:
            self.parent.ITKviewer.active_widget.delete_annotation(point)

        self.include_points = []
        self.exclude_points = []

        self.parent.segmentation_serie_manager.reset_preview(self.parent.ITKviewer.active_widget.serie_ID)
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
        self.remove = False
    
    def start_remove(self):
        self.button4.config(relief="sunken")
        self.remove = True

    def toggle_add(self):
        if self.button3.config('relief')[-1] == 'sunken':
            self.stop_add()
        else:
            self.stop_remove()
            self.start_add()

    def stop_add(self):
        self.button3.config(relief="raised")
        self.add = False

    def start_add(self):
        self.button3.config(relief="sunken")
        self.add = True

    def clear_segmentation(self):
        self.parent.ITKviewer.active_widget.clear_segmentation_mask_current_slice(self.layer_height)
        self.update_segmentation()

    def update_layer(self):
        self.layer_height = int(self.layer_entry.get())
        logging.debug("update layer to %s", self.layer_height)
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
        logging.debug("button1_press_event_image in manual segmentation")
        #get monitor cooridnates of mouse
        if self.mouse_in_itksegmentationframe(event) == False or self.ctrl_is_pressed(event) or self.shift_is_pressed(event) or self.ctrl_shift_is_pressed(event):
            logging.debug("mouse not in itksegmentationframe")
            return
        logging.debug(event.state - self.__previous_state)
        
        if self.auto_sam:
            self.accept_segmentation()
            return
        
        self.__previous_state = event.state  # remember the last keystroke state
        # print(self.layer_height)
        x, y = self.parent.ITKviewer.active_widget.get_mouse_location_dicom(event)
        # print(x, y)
        if self.button3.config('relief')[-1] == 'sunken':
            # print("add")
            self.add_include_point(x, y)
        elif self.button4.config('relief')[-1] == 'sunken':
            # print("remove")
            self.add_exclude_point(x, y)
        else:
            self.parent.ITKviewer.active_widget.set_segmentation_point_current_slice(int(x), int(y), self.layer_height)
        self.update_segmentation()

    def add_include_point(self, x, y):
        point = self.parent.ITKviewer.active_widget.set_annotation_point_current_slice(int(x), int(y), color="green", size=5)
        self.include_points.append(point)

    def add_exclude_point(self, x, y):
        point = self.parent.ITKviewer.active_widget.set_annotation_point_current_slice(int(x), int(y), color="red", size=5)
        self.exclude_points.append(point)

    def button3_press_event_image(self, event):
        logging.debug("button3_press_event_image in manual segmentation")
        #get monitor cooridnates of mouse
        if self.mouse_in_itksegmentationframe(event) == False or self.ctrl_is_pressed(event) or self.shift_is_pressed(event) or self.ctrl_shift_is_pressed(event):
            logging.debug("mouse not in itksegmentationframe")
            return
        logging.debug(event.state - self.__previous_state)
        self.__previous_state = event.state

        x, y = self.parent.ITKviewer.active_widget.get_mouse_location_dicom(event)

        if (self.button3.config('relief')[-1] == 'sunken' or self.button4.config('relief')[-1] == 'sunken') and not self.parent.ITKviewer.active_widget.is_mouse_on_image(event):
            visible_annotations = self.parent.ITKviewer.active_widget.annototation_under_mouse(event)
            if len(visible_annotations) > 0:
                for annotation in visible_annotations:
                    if annotation.unique_id in self.include_points:
                        self.parent.ITKviewer.active_widget.delete_annotation(annotation.unique_id)
                        self.include_points.remove(annotation.unique_id)
                    elif annotation.unique_id in self.exclude_points:
                        self.parent.ITKviewer.active_widget.delete_annotation(annotation.unique_id)
                        self.exclude_points.remove(annotation.unique_id)
        else:
            self.parent.ITKviewer.active_widget.set_segmentation_point_current_slice(int(x), int(y), 0)
        self.update_segmentation()

    def remove_annotation(self, annotation):
        if annotation.unique_id in self.include_points:
            self.include_points.remove(annotation.unique_id)
        elif annotation.unique_id in self.exclude_points:
            self.exclude_points.remove(annotation.unique_id)

    def update_segmentation(self):
        self.parent.ITKviewer.active_widget.update_image()
    
    def sam_segmentation(self, points_coords = np.empty((0, 2)), points_labels = np.empty((0,))):
        # https://github.com/facebookresearch/segment-anything/blob/main/notebooks/predictor_example.ipynb

        image = self.parent.ITKviewer.active_widget.get_image_from_HU_array(img_type = "RGB")
        self.sam_predictor.set_image(np.array(image))
        
        # NP_segmentation = self.parent.ITKviewer.active_widget.get_NP_seg_slice()
        # NP_segmentation == NP_segmentation == self.layer_height

        if not np.any(points_coords) and not np.any(points_labels):
            points_coords = np.empty((0, 2))
            points_labels = np.empty((0,)) # 1 is add to segmentation, 0 is remove from segmentation
            for point in self.include_points:
                annotation = self.parent.ITKviewer.active_widget.get_annotation(point)
                points_coords = np.append(points_coords, [annotation.ITK_coords[:-1]], axis=0)
                points_labels = np.append(points_labels, [1], axis=0)
            
            
            for point in self.exclude_points:
                annotation = self.parent.ITKviewer.active_widget.get_annotation(point)
                points_coords = np.append(points_coords, [annotation.ITK_coords[:-1]], axis=0)
                points_labels = np.append(points_labels, [0], axis=0)
            

        masks, scores, logits = self.sam_predictor.predict(point_coords=points_coords,
                            point_labels=points_labels, 
                            mask_input= self.previous_mask[None, :,:] if self.previous_mask is not None else None,
                            multimask_output=True)
        
        mask = masks[np.argmax(scores),:,:]
        if not self.auto_sam:
            self.previous_mask = logits[np.argmax(scores),:,:]
        else:
            self.reset_points()
        mask = sitk.GetImageFromArray(mask.astype(int))
        self.parent.ITKviewer.active_widget.set_segmentation_preview_mask_current_slice(self.layer_height, mask)
        self.update_segmentation()

    def destroy(self, event=None):
        self.parent.ITKviewer.active_widget.clear_segmentation_mask_current_slice(255)
        self.parent.ITKviewer.active_widget.clear_segmentation_mask_current_slice(254)
        print("destroy sam segmentation")
        self.parent.ITKviewer.active_widget.image_label.unbind('<ButtonPress-1>', self.bind1)
        self.parent.ITKviewer.active_widget.image_label.unbind('<ButtonPress-3>', self.bind2)
        self.parent.ITKviewer.active_widget.image_label.unbind('<Motion>', self.bind3)
        
    def enable_auto_sam(self):
        if self.auto_sam:
            self.auto_sam = False
            self.button6.config(relief="raised")
            self.parent.segmentation_serie_manager.reset_preview(self.parent.ITKviewer.active_widget.serie_ID)
        else:
            self.auto_sam = True
            self.button6.config(relief="sunken")
        self.parent.ITKviewer.active_widget.update_image()
        self.parent.focus_set()
        self.update_segmentation()
        self.parent.ITKviewer.active_widget.update_image()

    def motion_event_image(self, event):
        if self.auto_sam and self.mouse_in_itksegmentationframe(event):
            coords = self.parent.ITKviewer.active_widget.get_mouse_location_dicom(event)
            self.sam_segmentation(points_coords=np.array([coords]), points_labels=np.array([1]))

    def accept_segmentation(self):
        self.previous_mask = None
        if self.parent.segmentation_serie_manager.get_preview(self.parent.ITKviewer.active_widget.serie_ID) is not None:
            self.parent.ITKviewer.active_widget.accept_preview()  
            self.reset_points()  
            self.update_segmentation()
            self.parent.ITKviewer.active_widget.update_image()

main_class=SAM_segmentation