import logging
import os
import SimpleITK as sitk

class Segmentation_serie_manager:
    """placeholder"""
    def __init__(self, mainframe, DICOM_manager) -> None:
        self.mainframe = mainframe
        self.DICOM_manager = DICOM_manager
        self.segmentation_images = {}
        self.segmentation_stats = {}
        self.segmentation_preview_images = {}
        self.seg_label_dict : dict = {} # dictionary to store the labels of the segmentation

    def add_segmentation_serie(self, serie_ID, name = "default", label_dict = None):
        if serie_ID not in self.DICOM_manager.get_serie_IDs():
            logging.error('Serie ID not found')
            return
    
        if serie_ID not in self.segmentation_images:
            self.segmentation_images[serie_ID] = {}
            self.segmentation_stats[serie_ID] = {}
            print('Added segmentation serie: ' + serie_ID)
        
        if name == "preview":
            logging.warning('Preview is a reserved name')
            return

        if name in self.segmentation_images[serie_ID]:
            logging.warning('Segmentation name already exists, overwriting')
            
        self.segmentation_images[serie_ID][name] = sitk.Image(self.DICOM_manager.get_serie_size(serie_ID), sitk.sitkUInt8)
        self.segmentation_images[serie_ID][name].CopyInformation(self.DICOM_manager.get_serie_image(serie_ID))

        if label_dict is not None:
            self.set_label_dict(serie_ID, label_dict)


    @staticmethod
    def label_dict_is_valid(label_dict):
        if label_dict is None:
            return False
        if not isinstance(label_dict, dict):
            return False
        for key in label_dict:
            if not isinstance(key, int):
                return False
            if not isinstance(label_dict[key], str):
                return False
        return True


    def get_segmentation_names(self, serie_ID):
        seg_names = list(self.segmentation_images[serie_ID].keys())
        seg_names.remove("preview") if "preview" in seg_names else None
        return seg_names

    def get_serie_length(self, serie_ID, name = "default"):
        return self.segmentation_images[serie_ID][name].GetSize()[2]
    
    def get_image(self, serie_ID, name = "default", add_if_not_exist=False):
        if add_if_not_exist and serie_ID not in self.segmentation_images or name not in self.segmentation_images[serie_ID]:
            self.add_segmentation_serie(serie_ID, name)
        return self.segmentation_images[serie_ID][name]
    
    def get_segmentation(self, serie_ID, name = "default", add_if_not_exist=False):
        return self.get_image(serie_ID, name, add_if_not_exist)

    def save_segmentations(self, location):
        for serie_ID in self.segmentation_images:
            for segmentation_name in self.segmentation_images[serie_ID]:
                logging.info('Saving segmentation: ' + serie_ID)
                sitk.WriteImage(self.segmentation_images[serie_ID][segmentation_name], 
                                os.path.join(location, serie_ID , segmentation_name + '.nii.gz'))

    def load_segmentations(self, location):
        for file in os.listdir(location):
            if file.endswith('.nii.gz') and file[:-7] in self.DICOM_manager.get_serie_IDs():
                logging.info('Loading segmentation: ' + file)
                folder = os.path.basename(location)
                self.segmentation_images[folder][file[:-7]] = sitk.ReadImage(os.path.join(location, file))
                self.segmentation_images[folder][file[:-7]].CopyInformation(self.DICOM_manager.get_serie_image(file[:-7]))
                logging.info('Loaded segmentation: ' + file[:-7])
        self.mainframe.ITKviewer.update_images()

    def load_segmentation(self, segmentation, serie_id, name = "default"):
        if serie_id not in self.segmentation_images:
            self.segmentation_images[serie_id] = {}
            self.segmentation_stats[serie_id] = {}
            logging.info('Added segmentation serie: ' + serie_id)
        
        if name == "preview":
            logging.warning('Preview is a reserved name')
            return

        if name in self.segmentation_images[serie_id]:
            logging.warning('Segmentation name already exists, overwriting')
            
        if serie_id not in self.DICOM_manager.get_serie_IDs():
            logging.error('Serie ID not found')
            return
        self.segmentation_images[serie_id][name] = segmentation
        self.segmentation_images[serie_id][name].CopyInformation(self.DICOM_manager.get_serie_image(serie_id))
        self.segmentation_preview_images[serie_id] = None
        logging.info('Loaded segmentation: ' + serie_id)
        self.mainframe.ITKviewer.update_images()


    def get_stats(self, serie_ID, name = "default"):
        """placeholder"""
        self.segmentation_stats[serie_ID][name] = sitk.LabelStatisticsImageFilter()
        self.segmentation_stats[serie_ID][name].Execute(self.segmentation_images[serie_ID], self.DICOM_manager.get_serie_image(serie_ID))
        return self.segmentation_stats[serie_ID][name]
    
    def set_preview(self, serie_ID, preview: sitk.Image = None):
        if preview is None:
            logging.warning('No preview to set')
            return
        self.segmentation_images[serie_ID]["preview"] = preview

    def get_preview(self, serie_ID):
        if "preview" not in self.segmentation_images[serie_ID]:
            logging.debug('No preview to get')
            return None
        return self.segmentation_images[serie_ID]["preview"]
    
    def reset_preview(self, serie_ID):
        self.segmentation_images[serie_ID]["preview"] = None

    def has_preview(self, serie_ID) -> bool:
        if serie_ID not in self.segmentation_images:
            return False
        elif "preview" not in self.segmentation_images[serie_ID]:
            return False
        elif self.segmentation_images[serie_ID]["preview"] is None:
            return False
        return True
    
    def accept_preview(self, serie_ID, name = "default"):
        if serie_ID not in self.segmentation_images:
            logging.warning('No preview to accept, serie not found')
            return
        if name == "preview":
            logging.warning('Preview is a reserved name')
            return

        self.segmentation_images[serie_ID][name] = self.segmentation_images[serie_ID]["preview"]
        self.reset_preview(serie_ID)

    def get_label_dict(self, serie_ID):
        if serie_ID not in self.seg_label_dict:
            return None
        return self.seg_label_dict[serie_ID]
    
    def set_label_dict(self, serie_ID, label_dict):
        if not self.label_dict_is_valid(label_dict):
            logging.warning('Invalid label dict')
            return
        self.seg_label_dict[serie_ID] = label_dict

    def get_labels(self, serie_ID):
        if serie_ID not in self.seg_label_dict:
            return None
        return self.seg_label_dict[serie_ID].keys()
    
    def get_label(self, serie_ID, label):
        if serie_ID not in self.seg_label_dict:
            return None
        return self.seg_label_dict[serie_ID][label]
    
    def get_label_name(self, serie_ID, label):
        self.get_label(serie_ID, label)

    def set_label(self, serie_ID, label, name):
        if serie_ID not in self.seg_label_dict:
            self.seg_label_dict[serie_ID] = {}
        if not isinstance(label, int):
            logging.warning('Label must be an integer')
            return
        if not isinstance(name, str):
            logging.warning('Name must be a string')
            return
        self.seg_label_dict[serie_ID][label] = name

    def rename_label(self, serie_ID, label, name):
        self.set_label(serie_ID, label, name)

    def remove_label(self, serie_ID, label):
        if serie_ID not in self.seg_label_dict:
            return
        if label not in self.seg_label_dict[serie_ID]:
            return
        del self.seg_label_dict[serie_ID][label]