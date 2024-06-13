import logging
import uuid

class Annotation_manager:
    """placeholder"""
    def __init__(self, mainframe, DICOM_manager) -> None:
        self.mainframe = mainframe
        self.DICOM_manager = DICOM_manager
        self.annotations = {}

    def add_annotations_serie(self, serie_ID, annotation_class, should_be_Saved=True, **kwargs):
        unique_id = self.get_unique_id()
        if serie_ID in self.annotations.keys():
            self.annotations[serie_ID][unique_id] = { "annotation": annotation_class(unique_id, serie_ID, **kwargs), "should_be_Saved": should_be_Saved}
        else:
            self.annotations[serie_ID] = {}
            self.annotations[serie_ID][unique_id] = { "annotation": annotation_class(unique_id, serie_ID, **kwargs), "should_be_Saved": should_be_Saved}
        return unique_id
    
    def get_annotations(self, serie_ID):
        if serie_ID not in self.annotations.keys():
            logging.debug('Serie ID does not have any annotations')
            return []
        return self.annotations[serie_ID].keys()
    
    def get_unique_id(self):
        unique_id = uuid.uuid4().hex
        #probably overkill safety measure, but just in case there is a collision
        for serie_ID in self.annotations.keys():
            for annotation_unique_id in self.annotations[serie_ID].keys():
                if unique_id == annotation_unique_id:
                    return self.get_unique_id()
        return unique_id
    
    def get_annotation(self, serie_ID, annotation_ID):
        if serie_ID not in self.annotations.keys():
            logging.debug('Serie ID does not have any annotations')
            return None
        if annotation_ID not in self.annotations[serie_ID]:
            logging.debug('Annotation ID does not exist')
            return None
        return self.annotations[serie_ID][annotation_ID]["annotation"]
    
    def delete_annotation_ID(self, serie_ID, annotation_ID):
        if serie_ID not in self.DICOM_manager.get_serie_IDs():
            logging.warning('Serie ID does not exist')
            return None
        
        if serie_ID not in self.annotations.keys():
            logging.debug('Serie ID does not have any annotations')
            return None
        if annotation_ID not in self.annotations[serie_ID]:
            logging.debug('Annotation ID does not exist')
            return None
        del self.annotations[serie_ID][annotation_ID]

    def delete_all_serie_ID_annotations(self, serie_ID):
        if serie_ID not in self.annotations.keys():
            logging.debug('Serie ID does not have any annotations')
            return None
        del self.annotations[serie_ID]

    