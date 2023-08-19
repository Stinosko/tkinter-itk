import tkinter as tk  
from tkinter import ttk, Label, Menu, filedialog
import logging
import numpy as np
from PIL import Image, ImageTk
import math
from Utils import timer_func, PatchedFrame
import SimpleITK as sitk
from ITKviewerframe import ITKviewerFrame
import os
from DICOM_serie_instance import DICOM_serie_instance

class Segmentation_serie_manager:
    """placeholder"""
    def __init__(self, mainframe, DICOM_manager) -> None:
        self.mainframe = mainframe
        self.DICOM_manager = DICOM_manager
        self.segmentation_images = {}

    def add_segmentation_serie(self, serie_ID):
        if serie_ID in self.segmentation_images:
            logging.warning('Serie ID already exists')
            return
        self.segmentation_images[serie_ID] = sitk.Image(self.DICOM_manager.get_serie_size(serie_ID), sitk.sitkUInt8)
        self.segmentation_images[serie_ID].CopyInformation(self.DICOM_manager.get_serie_image(serie_ID))
    def get_segmentation_IDs(self, add_if_not_exist=False):
        return self.series_file_names.keys()

    def get_serie_length(self, serie_ID):
        return self.segmentation_images[serie_ID].GetSize()[2]
    
    def get_image(self, serie_ID, add_if_not_exist=False):
        if add_if_not_exist and serie_ID not in self.segmentation_images:
            self.add_segmentation_serie(serie_ID)
        return self.segmentation_images[serie_ID]