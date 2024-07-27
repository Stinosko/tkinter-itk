import os
import logging
import tkinter as tk  
import SimpleITK as sitk
from .DICOM_serie_instance import DICOM_serie_instance
from .DICOM_serie_manager import DICOM_serie_manager
from .DICOM_serie_instance_sitk import DICOM_serie_instance_sitk
from .DICOM_serie_instance_pydicom import DICOM_serie_instance_pydicom
from ..Utils import PatchedFrame
import pydicom
from pydicom.fileset import FileSet, RecordNode
from pydicom import dcmread, Dataset
from pydicom.uid import generate_uid
from pydicom.misc import is_dicom
from ..Utils import timer_func
from ..ITK_Utils import sitk_2_pydicom

class default_namespace:
    """ Use this information if info is not available"""
    PatientID = "Unknown"
    StudyID = "Unknown"


class DICOM_serie_manager_pydicom(DICOM_serie_manager):
    """placeholder"""
    def __init__(self, mainframe, **kwargs):
        super().__init__( mainframe, **kwargs)

        self.DICOM_DIR = None 
        self.fs = None
        self.file_instances = {}
        self.custom_sitk_images = {}

        if os.path.exists(os.path.join(os.getcwd(), "test-data")):
            self.DICOM_DIR = os.path.join(os.getcwd(), "test-data")
            self.load_DICOM_serie(DICOM_DIR = self.DICOM_DIR)
        else:
            self.DICOM_DIR = None
        # self.DICOM_DIR = os.path.join(os.path.dirname(__file__), "test-data")


    def load_DICOM_serie(self, DICOM_DIR = None, instance_list = None, image_name = None):
        if DICOM_DIR is None and instance_list is None:
            logging.warning("DICOM_DIR and instance_list are both None. Please provide one of them - returning")
            return
        
        self.file_instances = {}
        if DICOM_DIR is not None:
            self.DICOM_DIR = DICOM_DIR 
            
            if not os.path.exists(DICOM_DIR):
                logging.warning(f"Folder {DICOM_DIR} does not exist.")
                return

            self._getFileInstances(self.file_instances, DICOM_DIR)

        elif instance_list is not None:
            self.file_instances = instance_list

        # This is too slow
        # TODO: Multi-thread this, if possible
        # self.fs = FileSet()
        # self.fs = self._add_dicom_files_from_folder(DICOM_DIR, self.fs)

        self.reset_preview_frames()

    def load_image_serie(self, object: dict | sitk.Image = None, image_name: str = "placeholder", add: bool = False):
        if object is None:
            logging.warning("Object is None. Please provide an object - returning")
            return

        if isinstance(object, dict):
            # Merge the two dictionaries if add is True
            self.file_instances = object if add else { **self.file_instances, **object }
        
        if isinstance(object, sitk.Image):
            # Create a new serie_ID
            serie_ID = image_name
            if serie_ID in self.custom_sitk_images.keys():
                logging.warning(f"serie_ID {serie_ID} already exists. Overwriting.")
            self.custom_sitk_images[serie_ID] = object
            

        self.reset_preview_frames()

    def set_preview_frames(self):
        # Add 9-by-5 buttons to the frame
        
        self.DICOM_serie_instances = {}
        logging.info(f"Initalizing {len(self.file_instances)} DICOM series")
        for i, SerieID in enumerate(self.file_instances.keys()):
            self.DICOM_serie_instances[SerieID] = DICOM_serie_instance_pydicom(self.scrollable_frame, 
                                                                               fileInstances = self.file_instances[SerieID], 
                                                                               serie_ID = SerieID)
            self.DICOM_serie_instances[SerieID].grid(row=i, column=0, sticky='news')
        
        
        
        frame_offset = len(self.file_instances.keys())
        
        temp_folder = os.path.join(os.getcwd(), ".temp")
        
        for i, SerieID in enumerate(self.custom_sitk_images.keys()):
            if SerieID in self.file_instances.keys():
                logging.warning(f"serie_ID {SerieID} already exists in the file_instances!!!!!!!")
                continue
            
            writer = sitk.ImageFileWriter()
            
            writer.KeepOriginalImageUIDOn()
            writer.SetImageIO("NiftiImageIO")
            writer.SetFileName(os.path.join(temp_folder, SerieID + ".nii.gz"))
            writer.Execute(self.custom_sitk_images[SerieID])

            reader = sitk.ImageSeriesReader()
            reader.SetImageIO("NiftiImageIO")
            reader.SetFileNames([os.path.join(temp_folder, SerieID)])
            reader.LoadPrivateTagsOn()
            reader.MetaDataDictionaryArrayUpdateOn()
            
            itk_image = reader.Execute()
            print(itk_image.GetSize())
            print(itk_image.GetSpacing())
            print(itk_image.GetOrigin())
            print(itk_image.GetDirection())

            self.DICOM_serie_instances[SerieID] = DICOM_serie_instance_sitk(self.scrollable_frame,
                                                                            reader = reader,
                                                                            serie_ID = SerieID)
            self.DICOM_serie_instances[SerieID].grid(row=i + frame_offset, column=0, sticky='news')
        
        # Update buttons frames idle tasks to let tkinter calculate frame sizes
        self.update_idletasks()
        # Update te scrollbars
        self.canvas.config(scrollregion=self.canvas.bbox("all"))

    # This function is too slow
    # Only generate the fs when needed
    @timer_func(FPS_target=600)
    def _add_dicom_files_from_folder(self, folder_name, fs):
        try:
            SeriesNumber = fs.find_values("SeriesNumber")[-1] + 1
        except IndexError:
            SeriesNumber = 800
        
        for dicomfile in os.listdir(folder_name):
            if os.path.isdir(os.path.join(folder_name, dicomfile)):
                self._add_dicom_files_from_folder(os.path.join(folder_name, dicomfile), fs)
                continue
            if not is_dicom(os.path.join(folder_name, dicomfile)):
                logging.warning(f"File {dicomfile} is not a DICOM file.")
                continue
            custom_data = pydicom.dcmread(os.path.join(folder_name, dicomfile))

            try:
                fs.add(custom_data)
            except ValueError:

                # fs.add_custom(os.path.join(folder_name, "0.dcm"), leaf)
                if custom_data.PatientID == "":
                    custom_data.PatientID = default_namespace.PatientID
                if custom_data.StudyID == "":
                    custom_data.StudyID = default_namespace.StudyID
                if custom_data.SeriesNumber == "" or custom_data.SeriesNumber is None:
                    custom_data.SeriesNumber = SeriesNumber
                if custom_data.SeriesInstanceUID in fs.find_values("SeriesInstanceUID"):
                    custom_data.StudyInstanceUID = fs.find(SeriesInstanceUID = custom_data.SeriesInstanceUID)[0].StudyInstanceUID


                fs.add(custom_data)
        return fs
    
    def _getFileInstances(self, file_instances, path):
        """List all files in the directory, recursively. """

        for item in os.listdir(path):
            item = os.path.join(path, item)
            if os.path.isdir(item):
                self._getFileInstances(file_instances, item)
            elif is_dicom(item):
                item = pydicom.dcmread(item)
                if item.SeriesInstanceUID not in file_instances:
                    file_instances[item.SeriesInstanceUID] = []
                file_instances[item.SeriesInstanceUID].append(item)
            else:
                logging.warning(f"File {item} is not a DICOM file.")