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
        self.segmentation_stats = {}
        self.segmentation_preview_images = {}

    def add_segmentation_serie(self, serie_ID):
        if serie_ID in self.segmentation_images:
            logging.warning('Serie ID already exists')
            return
        self.segmentation_images[serie_ID] = sitk.Image(self.DICOM_manager.get_serie_size(serie_ID), sitk.sitkUInt8)
        self.segmentation_images[serie_ID].CopyInformation(self.DICOM_manager.get_serie_image(serie_ID))
    
    def get_segmentation_IDs(self, add_if_not_exist=False):
        return self.segmentation_images.keys()

    def get_serie_length(self, serie_ID):
        return self.segmentation_images[serie_ID].GetSize()[2]
    
    def get_image(self, serie_ID, add_if_not_exist=False):
        if add_if_not_exist and serie_ID not in self.segmentation_images:
            self.add_segmentation_serie(serie_ID)
        return self.segmentation_images[serie_ID]
    
    def save_segmentations(self, location):
        for serie_ID in self.segmentation_images:
            sitk.WriteImage(self.segmentation_images[serie_ID], os.path.join(location, serie_ID + '.nii.gz'))

    def load_segmentations(self, location):
        for file in os.listdir(location):
            if file.endswith('.nii.gz') and file[:-7] in self.DICOM_manager.get_serie_IDs():
                logging.info('Loading segmentation: ' + file)
                self.segmentation_images[file[:-7]] = sitk.ReadImage(os.path.join(location, file))
                self.segmentation_images[file[:-7]].CopyInformation(self.DICOM_manager.get_serie_image(file[:-7]))
                logging.info('Loaded segmentation: ' + file[:-7])
        self.mainframe.ITKviewer.update_images()

    def load_segmentation(self, segmentation, serie_id):
        if serie_id in self.segmentation_images:
            logging.warning('Segmentation name already exists, overwriting')
            
        if serie_id not in self.DICOM_manager.get_serie_IDs():
            logging.error('Serie ID not found')
            return
        self.segmentation_images[serie_id] = segmentation
        self.segmentation_images[serie_id].CopyInformation(self.DICOM_manager.get_serie_image(serie_id))
        self.segmentation_preview_images[serie_id] = None
        logging.info('Loaded segmentation: ' + serie_id)
        self.mainframe.ITKviewer.update_images()


    def get_stats(self, serie_ID):
        """placeholder"""
        self.segmentation_stats[serie_ID] = sitk.LabelStatisticsImageFilter()
        self.segmentation_stats[serie_ID].Execute(self.segmentation_images[serie_ID], self.DICOM_manager.get_serie_image(serie_ID))
        return self.segmentation_stats[serie_ID]
    
    def set_preview(self, serie_ID, preview: sitk.Image = None):
        if preview is None:
            logging.warning('No preview to set')
            return
        self.segmentation_preview_images[serie_ID] = preview

    def get_preview(self, serie_ID):
        if serie_ID not in self.segmentation_preview_images:
            logging.warning('No preview to get')
            return None
        return self.segmentation_preview_images[serie_ID]
    
    def reset_preview(self, serie_ID):
        self.segmentation_preview_images[serie_ID] = None

    
    def accept_preview(self, serie_ID):
        if serie_ID not in self.segmentation_preview_images:
            logging.warning('No preview to accept')
            return
        self.segmentation_images[serie_ID] = self.segmentation_preview_images[serie_ID]
        self.reset_preview(serie_ID)
