import re
import logging 
from tkinter import ttk, Label
import numpy as np
import tkinter as tk 
import SimpleITK as sitk
from PIL import Image, ImageTk
import pydicom.fileset
from ..Utils import PatchedFrame
from .DICOM_serie_instance import DICOM_serie_instance
import pydicom
from typing import List
import gc

class DICOM_serie_instance_pydicom(DICOM_serie_instance):
    """placeholder"""
    def __init__(self, mainframe, serie_ID, fileInstances, **kwargs):
        self.fileInstances: List[pydicom.fileset.FileInstance] = fileInstances
        self.sort_files()

        super().__init__( mainframe, serie_ID, **kwargs)


    def sort_files(self):
        self.fileInstances = sorted(self.fileInstances, key=lambda x: x.InstanceNumber)
        return self.fileInstances
    

    def get_sitk_image(self):
        array = self.get_pixel_array()

        # convert to SimpleITK image
        image = sitk.GetImageFromArray(array)
        image.SetOrigin(self.get_dicom_value( pytag = 'ImagePositionPatient'))

        logging.info(f"PixelSpacing: {self.get_dicom_value(pytag = 'PixelSpacing')}")
        spacing = self.get_dicom_value(pytag = 'PixelSpacing')

        if len(spacing) == 1:
            spacing = [spacing[0], spacing[0]]
            spacing.append(self.get_dicom_value(pytag = 'SpacingBetweenSlices') if self.get_dicom_value(pytag = 'SpacingBetweenSlices') is not None else 1)
        elif len(spacing) == 2:
            # slice spacing is not always available. If it isn't, 
            spacing.append(self.get_dicom_value(pytag = 'SpacingBetweenSlices') if self.get_dicom_value(pytag = 'SpacingBetweenSlices') is not None else 1)
        elif len(spacing) >= 4:
            logging.warn(f"PixelSpacing is potentially abnormal: {spacing}")
            pass
        
        logging.info(f"Spacing: {spacing}")
        image.SetSpacing(spacing[::-1]) # reverse the order of the spacing to match the order of the pixel array
        # x, y = self.fileInstances[0].get((0x0020, 0x0037)).value[0:3], self.fileInstances[0].get((0x0020, 0x0037)).value[3:6]
        x, y = self.get_dicom_value(pytag = 'ImageOrientationPatient')[0:3], self.get_dicom_value(pytag = 'ImageOrientationPatient')[3:6]
        origin_start = self.get_dicom_value(pytag = 'ImagePositionPatient')
        origin_end = self.get_dicom_value(pytag = 'ImagePositionPatient', slice_index = -1)
        z = np.array([origin_end[i] - origin_start[i] for i in range(3)])
        z = z / np.linalg.norm(z)
        image.SetDirection([x[0], y[0], z[0], x[1], y[1], z[1], x[2], y[2], z[2]])

        # Convert to 16 bit if necessary
        # 8 bit images result in overflow error when windowing is applied
        # TODO: fix underlying issue
        if image.GetPixelID() == sitk.sitkInt8:
            image = sitk.Cast(image, sitk.sitkInt16)
        elif image.GetPixelID() == sitk.sitkUInt8:
            image = sitk.Cast(image, sitk.sitkUInt16)

        return image

    def get_pixel_array(self):
        """ get_pixel_array()

        Get (load) the data that this DicomSeries represents, and return
        it as a numpy array. If this serie contains multiple images, the
        resulting array is 3D, otherwise it's 2D.

        If RescaleSlope and RescaleIntercept are present in the dicom info,
        the data is rescaled using these parameters. The data type is chosen
        depending on the range of the (rescaled) data.

        """
        # It's easy if no file or if just a single file
        if len(self.fileInstances) == 0:
            raise ValueError('Serie does not contain any files.')
        elif len(self.fileInstances) == 1:
            fileInstance = self.fileInstances[0]
            slice = self._getPixelDataFromDataset(fileInstance)
            return slice

        # Init data (using what the dicom packaged produces as a reference)
        ds = self.fileInstances[0]
        slice = self._getPixelDataFromDataset(ds)
        vol = np.zeros((len(self.fileInstances), slice.shape[0], slice.shape[1]), dtype=slice.dtype)
        vol[0] = slice

        # Fill volume
        ll = len(self.fileInstances)
        for z in range(1, ll):
            ds = self.fileInstances[z]
            vol[z] = self._getPixelDataFromDataset(ds)

        # Done
        gc.collect()
        return vol        
    
    @staticmethod
    def _getPixelDataFromDataset(ds):
        """ Get the pixel data from the given dataset. If the data
        was deferred, make it deferred again, so that memory is
        preserved. Also applies RescaleSlope and RescaleIntercept
        if available. """
        # Get original element
        el = ds['PixelData']

        # Get data
        data = ds.pixel_array

        # Remove data (mark as deferred)
        ds['PixelData'] = el
        del ds._pixel_array

        # Obtain slope and offset
        slope = 1
        offset = 0
        needFloats = False
        needApplySlopeOffset = False
        if 'RescaleSlope' in ds:
            needApplySlopeOffset = True
            slope = ds.RescaleSlope
        if 'RescaleIntercept' in ds:
            needApplySlopeOffset = True
            offset = ds.RescaleIntercept
        if int(slope) != slope or int(offset) != offset:
            needFloats = True
        if not needFloats:
            slope, offset = int(slope), int(offset)

        # Apply slope and offset
        if needApplySlopeOffset:

            # Maybe we need to change the datatype?
            if data.dtype in [np.float32, np.float64]:
                pass
            elif needFloats:
                data = data.astype(np.float32)
            else:
                # Determine required range
                minReq, maxReq = data.min(), data.max()
                minReq, maxReq = int(minReq), int(maxReq)
                minReq = min(
                    [minReq, minReq * slope + offset, maxReq * slope + offset])
                maxReq = max(
                    [maxReq, minReq * slope + offset, maxReq * slope + offset])

                # Determine required datatype from that
                dtype = None
                if minReq < 0:
                    # Signed integer type
                    maxReq = max([-minReq, maxReq])
                    if maxReq < 2 ** 7:
                        dtype = np.int8
                    elif maxReq < 2 ** 15:
                        dtype = np.int16
                    elif maxReq < 2 ** 31:
                        dtype = np.int32
                    else:
                        dtype = np.float32
                else:
                    # Unsigned integer type
                    if maxReq < 2 ** 8:
                        dtype = np.uint8
                    elif maxReq < 2 ** 16:
                        dtype = np.uint16
                    elif maxReq < 2 ** 32:
                        dtype = np.uint32
                    else:
                        dtype = np.float32

                # Change datatype
                if dtype != data.dtype:
                    data = data.astype(dtype)

            # Apply slope and offset
            data *= slope
            data += offset

        # Done
        return data


    def get_image_slice(self, slice_number):
        if self.ITK_image is None:
            self.ITK_image = self.get_sitk_image()
        return self.ITK_image[:,:,slice_number]
    
    def load_serie(self):
        if self.ITK_image is None:
            self.ITK_image = self.get_sitk_image()
            self.ITK_image.SetDirection((1,0,0,0,1,0,0,0,1))
            self.ITK_image.SetOrigin((0,0,0))
        return self.ITK_image

    def get_serie_size(self):
        if self.ITK_image is None:
            self.ITK_image = self.get_serie_image()
        size = self.ITK_image.GetSize()
        return tuple(size)
    
    def get_serie_image(self):
        if self.ITK_image is None:
            self.ITK_image = self.get_sitk_image()
            self.ITK_image.SetDirection((1,0,0,0,1,0,0,0,1))
            self.ITK_image.SetOrigin((0,0,0))
        return self.ITK_image
    
    def get_total_slices(self):
        if self.ITK_image is not None:
            self.total_slices = self.ITK_image.GetSize()[-1]
        else:
            self.load_serie()
            self.total_slices = self.ITK_image.GetSize()[-1]
        return self.total_slices

    def get_dicom_value(self, key = None, pytag = None, slice_index= 0):
        if self.fileInstances is None:
            return None
        slice_file = self.fileInstances[slice_index]
        if key is None and pytag is None:
            return None
        
        if pytag is not None:
            if hasattr(slice_file, pytag):
                return getattr(slice_file, pytag)
            else:
                return None

        if key is not None:
            sep = "|" if "|" in key else ","
            tag = [int(x, 16) for x in key.split(sep)]
            if tag in slice_file:
                return slice_file[tag].value