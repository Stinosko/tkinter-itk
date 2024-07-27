import os
import logging
import tkinter as tk  
import SimpleITK as sitk
from .DICOM_serie_instance_sitk import DICOM_serie_instance_sitk
from ..Utils import PatchedFrame
from .DICOM_serie_manager import DICOM_serie_manager


def GetGDCMSeriesIDs_recursive(DICOM_DIR, reader):
    """placeholder"""
    result = tuple()
    result = reader.GetGDCMSeriesIDs(DICOM_DIR)
    for directory in [ f.path for f in os.scandir(DICOM_DIR) if f.is_dir() ]:
        temp = GetGDCMSeriesIDs_recursive(directory, reader)
        if len(temp) > 0:
            result = result + temp
    return result


def GetGDCMSeriesIDs_recursive_cached(DICOM_DIR, reader):
    """Get the series IDs of a DICOM directory"""
    logging.debug(f"get serie ID in DICOM_DIR: {str(DICOM_DIR)}")
    result = {}
    serie_IDs = reader.GetGDCMSeriesIDs(str(DICOM_DIR))
    if len(serie_IDs) > 0:
        for serie_ID in serie_IDs:
            if serie_ID not in result:
                result[serie_ID] = str(DICOM_DIR)
            else:
                logging.warning(f"Series ID {serie_ID} exists in more than 1 directory")
    for directory in [ f.path for f in os.scandir(DICOM_DIR) if f.is_dir() ]:
        temp = GetGDCMSeriesIDs_recursive_cached(directory, reader)
        if len(temp) > 0:
            result = {**result, **temp}
    return result

class DICOM_serie_manager_sitk(DICOM_serie_manager):
    """placeholder"""
    def __init__(self, mainframe, **kwargs):
        super().__init__( mainframe, **kwargs)

        self.DICOM_DIR = None 

        self.reader = sitk.ImageSeriesReader()
        self.reader.MetaDataDictionaryArrayUpdateOn()
        self.reader.LoadPrivateTagsOn()
        
        self.series_file_names = {}
        if os.path.exists(os.path.join(os.getcwd(), "test-data")):
            self.DICOM_DIR = os.path.join(os.getcwd(), "test-data")
        else:
            self.DICOM_DIR = None
        # self.DICOM_DIR = os.path.join(os.path.dirname(__file__), "test-data")

        self.load_DICOM_serie(DICOM_DIR = self.DICOM_DIR)
        self.set_preview_frames()

    def load_DICOM_serie(self, DICOM_DIR = None, image_name = None):
        if DICOM_DIR is None:
            logging.warning("DICOM_DIR is None")
            return
        self.DICOM_DIR = DICOM_DIR
        series_file_names = {}
        series_IDs: dict = GetGDCMSeriesIDs_recursive_cached(DICOM_DIR, self.reader)
        # Check that we have at least one series
        if len(series_IDs) > 0 and image_name is None:
            for serie_ID in series_IDs.keys():
                dicom_names = sitk.ImageSeriesReader_GetGDCMSeriesFileNames(series_IDs[serie_ID], serie_ID)
                reader = sitk.ImageSeriesReader()
                reader.SetFileNames(dicom_names)
                reader.LoadPrivateTagsOn()
                reader.MetaDataDictionaryArrayUpdateOn()
                series_file_names[serie_ID] = reader
        elif image_name is not None:
            logging.warning("Untested code!")
            reader = sitk.ImageSeriesReader()
            reader.SetFileNames([image_name])
            reader.LoadPrivateTagsOn()
            reader.MetaDataDictionaryArrayUpdateOn()
            series_file_names[image_name] = reader
        else:
            logging.warning("Data directory does not contain any DICOM series.")
            return

        # check if they have the aqcuisition time key
        sort_by_acquisition_time = True
        sort_by_series_number = True
        
        for serie_ID in series_IDs.keys():
            try:
                series_file_names[serie_ID].Execute()
            except RuntimeError:
                print("Runtime error, skipping")
                del series_file_names[serie_ID]
                del self.DICOM_serie_instances[serie_ID]
                continue
            
            if not series_file_names[serie_ID].HasMetaDataKey(0, "0008|0032"):
                logging.warning(f"Series {serie_ID} does not have the key 0008|0032 (acquisition time).")
                sort_by_acquisition_time = False
            if not series_file_names[serie_ID].HasMetaDataKey(0, "0020|0011"):
                logging.warning(f"Series {serie_ID} does not have the key 0020|0011 (series number).")
                sort_by_series_number = False
        
            if not sort_by_acquisition_time and not sort_by_series_number:
                logging.warning(f"Series {serie_ID} does not have the keys 0008|0032 (acquisition time) or 0020|0011 (series number).")
                break
        
        if sort_by_acquisition_time and sort_by_series_number:
            # sort the series by key 0008|0032 (acquisition time) then by key 0020|0011 (series number)
            series_file_names = dict(sorted(series_file_names.items(), key=lambda item: (item[1].GetMetaData(0, "0008|0032"), item[1].GetMetaData(0, "0020|0011"))))

        if sort_by_acquisition_time:
            # sort the series by key 0008|0032 (acquisition time)
            series_file_names = dict(sorted(series_file_names.items(), key=lambda item: item[1].GetMetaData(0, "0008|0032")))

        elif sort_by_series_number:
            # sort the series by key 0020|0011 (series number)
            series_file_names = dict(sorted(series_file_names.items(), key=lambda item: item[1].GetMetaData(0, "0020|0011")))

        self.series_file_names = series_file_names

    def load_image_serie(self, image, image_name, add = False):
        if image is None:
            logging.warning("Image is None")
            return
        temp_folder = os.path.join(os.getcwd(), ".temp")
        if not add:
            self.DICOM_DIR = temp_folder
        writer = sitk.ImageFileWriter()
        
        writer.KeepOriginalImageUIDOn()
        writer.SetImageIO("NiftiImageIO")
        writer.SetFileName(os.path.join(self.DICOM_DIR, image_name + ".nii.gz"))
        writer.Execute(image)

        if not add: 
            self.series_file_names = {}
        reader = sitk.ImageSeriesReader()
        reader.SetImageIO("NiftiImageIO")
        reader.SetFileNames([os.path.join(self.DICOM_DIR, image_name)])
        reader.LoadPrivateTagsOn()
        reader.MetaDataDictionaryArrayUpdateOn()
        self.series_file_names[image_name] = reader
        return image_name

    def get_serie_reader(self, serie_ID):
        return self.series_file_names[serie_ID]

    def set_preview_frames(self):
        # Add 9-by-5 buttons to the frame
        
        self.DICOM_serie_instances = {}
        for i, serie_ID in enumerate(self.series_file_names.keys()):
            self.DICOM_serie_instances[serie_ID] = DICOM_serie_instance_sitk(self.scrollable_frame, serie_ID, self.get_serie_reader(serie_ID))
            self.DICOM_serie_instances[serie_ID].grid(row=i, column=0, sticky='news')
        
        # Update buttons frames idle tasks to let tkinter calculate frame sizes
        self.update_idletasks()
        # Update te scrollbars
        self.canvas.config(scrollregion=self.canvas.bbox("all"))
