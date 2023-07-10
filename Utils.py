import tkinter as tk  
import logging
import functools
import SimpleITK as sitk
import cv2
import numpy as np
import os
import uuid
import time




# https://stackoverflow.com/questions/38329996/enable-mouse-wheel-in-spinbox-tk-python
class Spinbox(tk.Spinbox):
    def __init__(self, *args, **kwargs):
        tk.Spinbox.__init__(self, *args, **kwargs)
        self.bind('<MouseWheel>', self.mouseWheel)
        self.bind('<Button-4>', self.mouseWheel)
        self.bind('<Button-5>', self.mouseWheel)

    def mouseWheel(self, event):
        if event.num == 5 or event.delta == -120:
            self.invoke('buttondown')
        elif event.num == 4 or event.delta == 120:
            self.invoke('buttonup')

from timeit import default_timer as timer



def timer_func(FPS_target=30):
    def decorator(func):
        def wrapper(*args, **kwargs):
            t1 = timer()
            result = func(*args, **kwargs)
            t2 = timer()
            if t2-t1 > 1/FPS_target: #30 FPS
                logging.info(f'{func.__name__} from {func.__module__} executed in {(t2-t1):.6f}s')
            return result
        return wrapper
    return decorator

class PatchedLabel(tk.Label):
    def unbind(self, sequence, funcid=None):
        '''
        See:
            http://stackoverflow.com/questions/6433369/
            deleting-and-changing-a-tkinter-event-binding-in-python
        '''

        if not funcid:
            self.tk.call('bind', self._w, sequence, '')
            return
        func_callbacks = self.tk.call(
            'bind', self._w, sequence, None).split('\n')
        new_callbacks = [
            l for l in func_callbacks if l[6:6 + len(funcid)] != funcid]
        self.tk.call('bind', self._w, sequence, '\n'.join(new_callbacks))
        self.deletecommand(funcid)

class PatchedFrame(tk.Frame):
    def unbind(self, sequence, funcid=None):
        '''
        See:
            http://stackoverflow.com/questions/6433369/
            deleting-and-changing-a-tkinter-event-binding-in-python
        '''

        if not funcid:
            self.tk.call('bind', self._w, sequence, '')
            return
        func_callbacks = self.tk.call(
            'bind', self._w, sequence, None).split('\n')
        new_callbacks = [
            l for l in func_callbacks if l[6:6 + len(funcid)] != funcid]
        self.tk.call('bind', self._w, sequence, '\n'.join(new_callbacks))
        self.deletecommand(funcid)

# https://stackoverflow.com/questions/43731784/tkinter-canvas-scrollbar-with-grid
class HoverButton(tk.Button):
    """ Button that changes color to activebackground when mouse is over it. """

    def __init__(self, master, **kw):
        super().__init__(master=master, **kw)
        self.default_Background = self.cget('background')
        self.hover_Background = self.cget('activebackground')
        self.bind('<Enter>', self.on_enter)
        self.bind('<Leave>', self.on_leave)

    def on_enter(self, e):
        self.config(background=self.hover_Background)

    def on_leave(self, e):
        self.config(background=self.default_Background)


def create_DICOM_files():
    # Create an empty 3D SimpleITK image
    image = sitk.Image([128, 128, 128], sitk.sitkUInt8)

    # Get the number of slices
    num_slices = image.GetSize()[2]

    # Create an empty list to store the modified slices
    slices_with_numbers = []
    np_array = np.empty(image.GetSize(), dtype=np.int16)
    # Loop over each slice
    for i in range(num_slices):
        # Extract the slice
        
        # Normalize the slice array for visualization
        np_array[i, :, :] = cv2.normalize(np_array[i, :, :], None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
        
        # Write the slice number on the slice
        cv2.putText(np_array[i, :, :], str(i), (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

    new_img = sitk.GetImageFromArray(np_array)
    new_img.SetSpacing([2.5, 3.5, 4.5])

    writer = sitk.ImageFileWriter()
    # Use the study/series/frame of reference information given in the meta-data
    # dictionary and not the automatically generated information from the file IO
    writer.KeepOriginalImageUIDOn()

    modification_time = time.strftime("%H%M%S")
    modification_date = time.strftime("%Y%m%d")

    # Copy some of the tags and add the relevant tags indicating the change.
    # For the series instance UID (0020|000e), each of the components is a number,
    # cannot start with zero, and separated by a '.' We create a unique series ID
    # using the date and time. Tags of interest:
    direction = new_img.GetDirection()
    series_tag_values = [
        ("0008|0031", modification_time),  # Series Time
        ("0008|0021", modification_date),  # Series Date
        ("0008|0008", "DERIVED\\SECONDARY"),  # Image Type
        (
            "0020|000e",
            "1.2.826.0.1.3680043.2.1125."
            + modification_date
            + ".1"
            + modification_time,
        ),  # Series Instance UID
        (
            "0020|0037",
            "\\".join(
                map(
                    str,
                    (
                        direction[0],
                        direction[3],
                        direction[6],
                        direction[1],
                        direction[4],
                        direction[7],
                    ),
                )
            ),
        ),  # Image Orientation
        # (Patient)
        ("0008|103e", "Created-SimpleITK"),  # Series Description
    ]

    # Write slices to output directory
    list(
        map(
            lambda i: writeSlices(series_tag_values, new_img, os.path.join("test-data","dicom_files"), i, writer= writer),
            range(new_img.GetDepth()),
        )
    )

    
def writeSlices(series_tag_values, new_img, out_dir, i, writer):
    image_slice = new_img[:, :, i]

    # Tags shared by the series.
    list(
        map(
            lambda tag_value: image_slice.SetMetaData(
                tag_value[0], tag_value[1]
            ),
            series_tag_values,
        )
    )

    # Slice specific tags.
    #   Instance Creation Date
    image_slice.SetMetaData("0008|0012", time.strftime("%Y%m%d"))
    #   Instance Creation Time
    image_slice.SetMetaData("0008|0013", time.strftime("%H%M%S"))

    # Setting the type to CT so that the slice location is preserved and
    # the thickness is carried over.
    image_slice.SetMetaData("0008|0060", "CT")

    # (0020, 0032) image position patient determines the 3D spacing between
    # slices.
    #   Image Position (Patient)
    image_slice.SetMetaData(
        "0020|0032",
        "\\".join(map(str, new_img.TransformIndexToPhysicalPoint((0, 0, i)))),
    )
    #   Instance Number
    image_slice.SetMetaData("0020|0013", str(i))

    # Write to the output directory and add the extension dcm, to force
    # writing in DICOM format.
    writer.SetFileName(os.path.join(out_dir, str(i) + ".dcm"))
    writer.Execute(image_slice)

def create_NII_file():
    # Create an empty 3D SimpleITK image
    image = sitk.Image([128, 128, 128], sitk.sitkUInt8)

    # Get the number of slices
    num_slices = image.GetSize()[2]

    # Create an empty list to store the modified slices
    slices_with_numbers = []

    # Loop over each slice
    for i in range(num_slices):
        # Extract the slice
        slice = image[:,:,i]
        
        # Convert the slice to a numpy array
        slice_array = sitk.GetArrayFromImage(slice)
        
        # Normalize the slice array for visualization
        slice_array = cv2.normalize(slice_array, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
        
        # Write the slice number on the slice
        cv2.putText(slice_array, str(i), (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        
        # Convert the numpy array back to a SimpleITK image
        slice_with_number = sitk.GetImageFromArray(slice_array)
        
        # Add the slice to the list
        slices_with_numbers.append(slice_with_number)

    # Stack the slices to create a 3D image
    image_with_numbers = sitk.JoinSeries(slices_with_numbers)

    # Save the 3D image
    sitk.WriteImage(image_with_numbers, 'image_with_numbers.nii')
