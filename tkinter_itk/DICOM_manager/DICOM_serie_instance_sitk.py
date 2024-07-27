import re
import logging 
from tkinter import ttk, Label
import numpy as np
import tkinter as tk 
import SimpleITK as sitk
from PIL import Image, ImageTk
import pydicom
from ..Utils import PatchedFrame
from .DICOM_serie_instance import DICOM_serie_instance

class DICOM_serie_instance_sitk(DICOM_serie_instance):
    """placeholder"""
    def __init__(self, mainframe, serie_ID, reader, **kwargs):
        self.reader = reader
        super().__init__( mainframe, serie_ID, **kwargs)

        if self.reader.GetImageIO() == "":
            # self.total_slices = len(self.reader.GetFileNames())
            # self.preview_reader = sitk.ImageFileReader()
            # self.preview_reader.SetFileName(self.reader.GetFileNames()[round(self.total_slices/2) - 1])
            # self.preview_ITK_image = self.preview_reader.Execute()
            pass

            # self.preview_image = sitk.GetArrayFromImage(self.preview_ITK_image)
            # self.preview_image = normalize_np_array_between_0_and_255(self.preview_image[0,:,:])
            # self.preview_image = self.preview_image.astype(np.uint8)
            # self.preview_image = Image.fromarray(self.preview_image)
            # self.preview_image = ImageTk.PhotoImage(self.preview_image)

        else:
            self.ITK_image = self.reader.Execute()
            if self.ITK_image.GetDimension() == 4:
                self.ITK_image = self.ITK_image[:,:,:,0]
            elif self.ITK_image.GetDimension() > 4:
                logging.error("Image dimension is greater than 4. Cannot be displayed.")
                raise ValueError("Image dimension is greater than 4. Cannot be displayed.")
            elif self.ITK_image.GetDimension() == 2:
                self.ITK_image = sitk.JoinSeries([self.ITK_image])
            elif self.ITK_image.GetDimension() == 3:
                pass
            elif self.ITK_image.GetDimension() == 1:
                logging.error("Image dimension is less than 2. Cannot be displayed.")
                raise ValueError("Image dimension is less than 2. Cannot be displayed.")
            
            self.ITK_image.SetDirection((1,0,0,0,1,0,0,0,1))
            self.ITK_image.SetOrigin((0,0,0))
            # self.total_slices = self.ITK_image.GetSize()[-1]
            # self.preview_reader = None
            # self.preview_ITK_image = None

            # self.preview_image = sitk.GetArrayFromImage(self.ITK_image[:,:,round(self.total_slices/2) - 1])
            
            # self.preview_image = normalize_np_array_between_0_and_255(self.preview_image)
            # self.preview_image = self.preview_image.astype(np.uint8)
            # self.preview_image = Image.fromarray(self.preview_image)
            # self.preview_image = ImageTk.PhotoImage(self.preview_image)

        # self.preview_label.config( image=self.preview_image, width=150, height=150)

        if self.reader.GetImageIO() == "":
            self.button.config(text=self.serie_ID)
        elif self.reader.HasMetaDataKey(key = "0008|103e", slice = 0):
            self.button.config(text=self.reader.GetMetaData(key = "0008|103e", slice = 0))
        else:
            self.button.config(text=self.serie_ID)
            
        self.button.grid(row=1, column=0)


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
    
    def load_serie(self):
        if self.ITK_image is None:
            self.ITK_image = self.reader.Execute()
            self.ITK_image.SetDirection((1,0,0,0,1,0,0,0,1))
            self.ITK_image.SetOrigin((0,0,0))
        return self.ITK_image

    def get_serie_size(self):
        if self.ITK_image is None:
            first_slice_reader = sitk.ImageFileReader()
            first_slice_reader.SetFileName(self.reader.GetFileNames()[0])
            size = list(first_slice_reader.Execute().GetSize())
            size[-1] = self.total_slices
        else:
            size = self.ITK_image.GetSize()
        return tuple(size)
    
    def get_serie_image(self):
        if self.ITK_image is None:
            self.ITK_image = self.reader.Execute()
            self.ITK_image.SetDirection((1,0,0,0,1,0,0,0,1))
            self.ITK_image.SetOrigin((0,0,0))
        return self.ITK_image
    
    def get_total_slices(self):
        if self.reader.GetImageIO() == "":
            self.total_slices = len(self.reader.GetFileNames())
        elif self.ITK_image is not None:
            self.total_slices = self.ITK_image.GetSize()[-1]
        else:
            self.load_serie()
            self.total_slices = self.ITK_image.GetSize()[-1]
        return self.total_slices

        
    def get_dicom_value(self, key, pytag, slice_index= 0):
        if self.reader is None:
            return None
        
        if key is None and pytag is None:
            return None
        
        if pytag is not None:
            tag_hex = pydicom.datadict.tag_for_keyword(pytag)
            tag  = [tag_hex >> 16, tag_hex & 0xFFFF].join("|")
            tag = "{:04x}|{:04x}".format(tag[0], tag[1])

            if self.reader.HasMetaDataKey(key = tag, slice = slice_index):
                return self.reader.GetMetaData(key = tag, slice = slice_index)
            else:
                return None
        
        if key is not None:
            if self.reader.HasMetaDataKey(key = key, slice = slice_index):
                return self.reader.GetMetaData(key = key, slice = slice_index)
            else:
                return None
        