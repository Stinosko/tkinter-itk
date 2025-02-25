import tkinter as tk  
import logging
from ..Utils import Spinbox
import SimpleITK as sitk
import ast

def bind_event_data(widget, sequence, func, add = None):
    def _substitute(*args):
        e = lambda: None #simplest object with __dict__
        e.data = ast.literal_eval(args[0] ) 
        if type(e.data) == dict:
            for key, value in e.data.items():
                setattr(e, key, value)
        else:
            logging.warning("data is not a dict")
            logging.debug(e.data)
            raise ValueError("data is not a dict")
        e.widget = widget
        return (e,)

    funcid = widget._register(func, _substitute, needcleanup=1)
    cmd = '{0}if {{"[{1} %d]" == "break"}} break\n'.format('+' if add else '', funcid)
    widget.tk.call('bind', widget._w, sequence, cmd)
    return funcid

class manual_segmentation:
    name_short = "manual"
    name_long = "manual segmentation"
    
    def __init__(self, parent, **kwargs):
        self.parent = parent
        self.layer_height = 1
    
    def load_plugin(self):
        self.parent.segmentation_modes.append(self.__class__.__name__)

    def __str__(self) -> str:
        return "ITK viewer plugin manual segmentation"
    
    def get_segmentation_options(self, parent):
        self.__previous_state = 0

        self.frame = tk.Frame(parent)
        self.frame.grid(row=0, column=1, sticky=tk.E + tk.W, pady=1)
        self.start_click_location_X = None
        self.start_click_location_Y = None
        self.time_last_event = 0


        self.layer_frame = tk.Frame(self.frame)
        self.layer_label = tk.Label(self.layer_frame, text="Layer")
        self.layer_label.grid(row=0, column=0, sticky=tk.E + tk.W, pady=1)
        self.layer_entry = Spinbox(self.layer_frame, from_=1, to=self.parent.ITKviewer.active_widget.max_layers, width=1, command=self.update_layer)
        self.layer_entry.grid(row=1, column=0, sticky=tk.E + tk.W, pady=1)
        self.layer_entry.bind('<Return>', lambda event: self.update_layer())
        self.layer_frame.grid(row=0, column=0, sticky=tk.E + tk.W, pady=1)

        self.button = tk.Button(self.frame, text="Clear segmentation", command=self.clear_segmentation)
        self.button.grid(row=0, column=1, sticky=tk.E + tk.W, pady=1)

        self.button2 = tk.Button(self.frame, text="Fill holes", command=self.fill_holes)
        self.button2.grid(row=0, column=2, sticky=tk.E + tk.W, pady=1)

        self.button3 = tk.Button(self.frame, text="Keep largest blob", command=self.keep_largest_blob)
        self.button3.grid(row=0, column=3, sticky=tk.E + tk.W, pady=1)
        
        self.bind1 = self.parent.ITKviewer.active_widget.image_label.bind('<ButtonPress-1>', self.button1_press_event_image, add = "+")
        self.bind2 = self.parent.ITKviewer.active_widget.image_label.bind('<ButtonPress-3>', self.button3_press_event_image, add = "+")
        self.bind3 = bind_event_data(self.parent.ITKviewer.active_widget.image_label, '<<DragEvent>>', self.drag_event_mouse, add = "+")
        self.bind4 = bind_event_data(self.parent.ITKviewer.active_widget.image_label, '<<StartDragEvent>>', self.drag_event_mouse, add = "+")
        self.bind5 = bind_event_data(self.parent.ITKviewer.active_widget.image_label, '<<StopDragEvent>>', self.stop_drag_event_mouse, add = "+")

        # self.bind3 = self.parent.ITKviewer.active_widget.image_label.bind('<<DragEvent>>', self.drag_event_mouse, add = "+")
        # self.bind4 = self.parent.ITKviewer.active_widget.image_label.bind('<<StartDragEvent>>', self.drag_event_mouse, add = "+")
        # self.bind5 = self.parent.ITKviewer.active_widget.image_label.bind('<<StopDragEvent>>', self.stop_drag_event_mouse, add = "+")
        self.frame.bind("<Destroy>", self.destroy)
        
        return self.frame
    
    def test(self, event):
        logging.warning("test")

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

    def drag_event_mouse(self, event):
        logging.debug("drag_event_mouse in manual segmentation")
        #get monitor cooridnates of mouse
        if self.start_click_location_X is None or self.start_click_location_Y is None:
            self.start_click_location_X = event.x
            self.start_click_location_Y = event.y
            return
        
        if event.time < self.time_last_event:
            logging.debug("Recieved event older than last processed event, dropping event")
            return

        dicom_start = self.parent.ITKviewer.active_widget.get_mouse_location_dicom(coords=(self.start_click_location_X, self.start_click_location_Y))
        dicom_end = self.parent.ITKviewer.active_widget.get_mouse_location_dicom(coords=(event.x, event.y))

        # check if dicom_start and dicom_end are valid
        if dicom_start is None or dicom_end is None:
            logging.debug("dicom_start or dicom_end is None")
            self.stop_drag_event_mouse(event)
            return
        elif dicom_start[0] < 0 or dicom_start[1] < 0 or dicom_end[0] < 0 or dicom_end[1] < 0:
            logging.debug("dicom_start or dicom_end out of bounds")
            self.stop_drag_event_mouse(event)
            return
        elif dicom_start[0] >= self.parent.ITKviewer.active_widget.ITK_image.GetSize()[0] or dicom_start[1] >= self.parent.ITKviewer.active_widget.ITK_image.GetSize()[1] or dicom_end[0] >= self.parent.ITKviewer.active_widget.ITK_image.GetSize()[0] or dicom_end[1] >= self.parent.ITKviewer.active_widget.ITK_image.GetSize()[1]:
            logging.debug("dicom_start or dicom_end out of bounds")
            self.stop_drag_event_mouse(event)
            return

        self.start_click_location_X = event.x
        self.start_click_location_Y = event.y
        
        # print(dicom_start, dicom_end)
        if event.num == 1:
            self.parent.ITKviewer.active_widget.set_segmentation_line_current_slice(int(dicom_start[0]), int(dicom_start[1]), int(dicom_end[0]), int(dicom_end[1]), self.layer_height)
        elif event.num  == 3:
            self.parent.ITKviewer.active_widget.set_segmentation_line_current_slice(int(dicom_end[0]), int(dicom_end[1]), int(dicom_start[0]), int(dicom_start[1]), 0)



    def stop_drag_event_mouse(self, event):
        self.start_click_location_X = None
        self.start_click_location_Y = None

    def button1_press_event_image(self, event):
        logging.debug("button1_press_event_image in manual segmentation")
        #get monitor cooridnates of mouse
        if self.mouse_in_itksegmentationframe(event) == False or self.ctrl_is_pressed(event) or self.shift_is_pressed(event) or self.ctrl_shift_is_pressed(event):
            logging.debug("mouse not in itksegmentationframe")
            return
        logging.debug(event.state - self.__previous_state)
        self.__previous_state = event.state  # remember the last keystroke state

        x, y = self.parent.ITKviewer.active_widget.get_mouse_location_dicom(event)
        self.parent.ITKviewer.active_widget.set_segmentation_point_current_slice(int(x), int(y), self.layer_height)
        self.update_segmentation()

    def button3_press_event_image(self, event):
        logging.debug("button3_press_event_image in manual segmentation")
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
    
    def destroy(self, event=None):
        print("destroy manual segmentation")
        self.parent.ITKviewer.active_widget.image_label.unbind('<ButtonPress-1>', self.bind1)
        self.parent.ITKviewer.active_widget.image_label.unbind('<ButtonPress-3>', self.bind2)
        self.parent.ITKviewer.active_widget.image_label.unbind('<<DragEvent>>', self.bind3)
        self.parent.ITKviewer.active_widget.image_label.unbind('<<StartDragEvent>>', self.bind4)
        self.parent.ITKviewer.active_widget.image_label.unbind('<<StopDragEvent>>', self.bind5)

    def fill_holes(self):
        logging.debug("fill holes")
        ITK_seg_image = self.parent.ITKviewer.active_widget.get_segmentation_mask_current_slice().__copy__()
        ITK_seg_image = sitk.BinaryFillhole(ITK_seg_image, foregroundValue=self.layer_height)
        self.parent.ITKviewer.active_widget.set_segmentation_mask_current_slice(layer_height = self.layer_height, mask = ITK_seg_image)

    def keep_largest_blob(self):
        logging.debug("keep largest blob")
        ITK_seg_image: sitk.Image = self.parent.ITKviewer.active_widget.get_segmentation_mask_current_slice().__copy__()
        binary_image = sitk.BinaryThreshold(ITK_seg_image, lowerThreshold=self.layer_height, upperThreshold=self.layer_height, insideValue=1, outsideValue=0)
        # https://discourse.itk.org/t/simpleitk-extract-largest-connected-component-from-binary-image/4958
        component_image = sitk.ConnectedComponent(binary_image)
        sorted_component_image = sitk.RelabelComponent(component_image, sortByObjectSize=True)
        largest_component_binary_image = sorted_component_image == 1
        ITK_seg_image_np = sitk.GetArrayFromImage(ITK_seg_image)
        largest_component_binary_image_np = sitk.GetArrayFromImage(largest_component_binary_image)
        pixels_to_remove = (ITK_seg_image_np == self.layer_height) & (largest_component_binary_image_np == 0)
        ITK_seg_image_np[pixels_to_remove] = 0
        largest_component_image = sitk.GetImageFromArray(ITK_seg_image_np)



        self.parent.ITKviewer.active_widget.set_segmentation_mask_current_slice(layer_height = self.layer_height, mask = largest_component_image)

main_class=manual_segmentation