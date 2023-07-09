import tkinter as tk  
import logging
import functools
import SimpleITK as sitk
import cv2
import numpy as np
import os
import uuid





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

    # Create a directory to store the DICOM files
    os.makedirs('dicom_files', exist_ok=True)

    # Save the 3D image as a series of DICOM files
    writer = sitk.ImageFileWriter()
    writer.KeepOriginalImageUIDOn()

    # Generate a new Series Instance UID
    series_uid = str(uuid.uuid4())

    for i in range(image_with_numbers.GetDepth()):
        image_slice = image_with_numbers[:,:,i]
        
        # Set the Series Instance UID
        image_slice.SetMetaData('0020|000e', series_uid)
        
        # Tags shared by the series.
        writer.SetFileName(os.path.join('dicom_files', 'slice_{0}.dcm'.format(i)))
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
