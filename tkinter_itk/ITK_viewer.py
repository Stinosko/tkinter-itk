import logging
import tkinter as tk
from tkinter import Menu, ttk
import os 
import SimpleITK as sitk

from .menu.fileMenu import FileMenu
from .menu.helpMenu import HelpMenu
from .menu.segmentationMenu import SegemntationMenu

from .topbar import Topbar
from .ImagesFrameManager import imagesFrameManager, example_dual_frame_list
from .DICOM_manager.DICOM_serie_manager_sitk import DICOM_serie_manager_sitk
from .DICOM_manager.DICOM_serie_manager_pydicom import DICOM_serie_manager_pydicom
from .segmentation_serie_manager import Segmentation_serie_manager
from .Annotation_manager import Annotation_manager
from .Utils import AutoScrollbar
#import progressbar

from typing import List


logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)


#https://packaging.python.org/en/latest/guides/creating-and-discovering-plugins/
import importlib
import pkgutil
import logging
import datetime

discovered_plugins = {}

plugin_path = os.path.join(os.path.dirname(__file__), 'plugins')

for finder, name, ispkg in pkgutil.iter_modules([plugin_path]):
    if name.startswith('itk_viewer_plugin_'):
        try:
            module = importlib.import_module(f".plugins.{name}", package="tkinter_itk")
            discovered_plugins[name[18:]] = module.main_class
        except ModuleNotFoundError as e:
            logging.error(f"Failed to import plugin: {e}")
        except AttributeError as e:
            logging.error(f"Failed to import plugin, did you inlcude a main_class?\nError code: {e}")
        except Exception as e:
            logging.error(f"Failed to import plugin: {e}")



logging.info(discovered_plugins)

class Colors:
    """ Colors to RGB value """
    Black   = [0, 0, 0, 125]
    White   = [255, 255, 255, 125]
    Red     = [255, 0, 0, 125]
    Lime    = [0, 255, 0, 125]
    Blue    = [0, 0, 255, 125]
    Yellow  = [255, 255, 0, 125]
    Cyan    = [0, 255, 255, 125]
    Magenta = [255, 0, 255, 125]
    Silver  = [192, 192, 192, 125]
    Gray    = [128, 128, 128, 125]
    Maroon  = [128, 0, 0, 125]
    Olive   = [128, 128, 0, 125]
    Green   = [0, 128, 0, 125]
    Purple  = [128, 0, 128, 125]
    Teal    = [0, 128, 128, 125]
    Navy    = [0, 0, 128, 125]



class ITKWindow(ttk.Frame):
    """ Main window class """
    plugins = {}
    
    segmentation_modes = ["None"]
    current_segmentation_mode = segmentation_modes[0]

    filemenu: FileMenu  
    helpmenu: HelpMenu
    segmentationmenu: SegemntationMenu
    label1: Topbar
    DICOM_serie_manager: DICOM_serie_manager_sitk
    annotation_manager: Annotation_manager
    segmentation_serie_manager: Segmentation_serie_manager
    ITKviewer: imagesFrameManager
    label3: tk.Label



    def __init__(self, mainframe, threading = False, image_label_layout= example_dual_frame_list, *args, **kwargs):
        """ Initialize the main Frame """
        ttk.Frame.__init__(self, master=mainframe, *args, **kwargs)
        self.load_plugins()
        self.mainframe = mainframe
        self.threading = threading
        self.current_segmentation_mode = tk.StringVar(self)
        self.current_segmentation_mode.set(self.segmentation_modes[0])
        #TO DO: https://stackoverflow.com/a/41679642
        self.menubar = Menu(self)
        
        self.filemenu = FileMenu(self, self.menubar)
        self.menubar.add_cascade(label="Dicom", menu=self.filemenu)

        self.segmentationmenu = SegemntationMenu(self, self.menubar)
        self.menubar.add_cascade(label="Segmentation", menu=self.segmentationmenu)

        self.menubar.add_separator()

        self.helpmenu = HelpMenu(self, self.menubar)
        self.menubar.add_cascade(label="Help", menu=self.helpmenu)
        
        self.nametowidget('.').config(menu = self.menubar)

        self.label1 = Topbar(self, self)
        self.label1.grid(row=0, column=0, columnspan = 3, pady=5, sticky = tk.W + tk.E)

        self.DICOM_serie_manager = DICOM_serie_manager_sitk(self, bg="blue")
        self.DICOM_serie_manager.grid(row=1, column=0, pady=1, sticky = tk.N + tk.S)
        
        self.annotation_manager = Annotation_manager(self, self.DICOM_serie_manager)
        self.segmentation_serie_manager = Segmentation_serie_manager(self, self.DICOM_serie_manager)

        self.ITKviewer = imagesFrameManager(self, image_label_layout = image_label_layout, bg = "yellow", parent=self, threading=threading) # create ITK Frame
        # self.ITKviewer = ITKviewerFrame(self.mainframe, bg = "red") # create ITK Frame
        # self.ITKviewer = ITKsegmentationFrame(self.mainframe, bg = "red") # create ITK Frame
        self.ITKviewer.grid(row=1, column=1, columnspan = 2, sticky= tk.N + tk.S + tk.E + tk.W)  # show ITK 
        
        self.ITKviewer.rowconfigure(0, weight=1)
        self.ITKviewer.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        self.columnconfigure(1, weight=1)


        self.label3 = tk.Label(self, text="Placeholder bottom", bg="green")
        self.label3.grid(row=2, column=0, columnspan = 3, pady=1, sticky = tk.W + tk.E)

        self.np_CT_array = None

    def new_image_input(self, image: sitk.Image = None, image_name: str = None, add = False) -> str:
        """ Placeholder"""
        self.update_idletasks()
        logging.info('Importing patient data')
        if image is None:
            DICOM_DIR = self.filemenu.get_filename()
            logging.debug(f'Importing patient data: {DICOM_DIR}')
            if add:
                logging.warning(f'Adding not implemented yet for DICOM_DIR')
            self.DICOM_serie_manager.load_DICOM_serie(DICOM_DIR, image_name)
        else:
            logging.debug(f'Importing patient data: {image_name}')
            self.DICOM_serie_manager.load_image_serie(image, image_name, add = add)
        self.DICOM_serie_manager.reset_preview_frames()
        return image_name

    def load_dicom_folder(self):
        DICOM_DIR = self.filemenu.get_filename()
        self.DICOM_serie_manager.load_DICOM_serie(DICOM_DIR)

    def load_segmentation(self, segmentation: sitk.Image = None, serie_id: str = None):
        """ Placeholder"""
        self.update_idletasks()
        logging.info('Importing segmentation')
        if serie_id is None:
            logging.error('No segmentation name given')
            return
        if segmentation is None:
            logging.error('No segmentation given')
            return
        logging.debug(f'Importing segmentation: {serie_id}')
        self.segmentation_serie_manager.load_segmentation(segmentation, serie_id)
        return serie_id

    def load_plugins(self):
        """ Placeholder"""
        logging.info('Loading plugins')
        for plugin in discovered_plugins:
            self.plugins[plugin] = discovered_plugins[plugin](self)
            self.plugins[plugin].load_plugin()
        logging.info(f'Loaded plugins: {self.plugins}')

    def segmentation_mode_changed(self, *args):
        """ Placeholder"""
        logging.info(f'Segmentation mode changed to: {self.current_segmentation_mode.get()}')
        

    def save_segmentations(self):
        """ Placeholder"""
        logging.info('Saving segmentations')
        self.segmentation_serie_manager.save_segmentations(location = self.segmentationmenu.segmentation_folder)

    def load_segmentations(self):
        """ Placeholder"""
        logging.info('Loading segmentations')
        self.segmentation_serie_manager.load_segmentations(location = self.segmentationmenu.segmentation_folder)
    
    async def update(self) -> None:
        
        await self.ITKviewer.update_image_if_needed()
        return super().update()


class orthancWindow(ttk.Frame):
    """ Orthanc window class """
    def __init__(self, mainframe, orthanc, *args, **kwargs):
        """ Initialize the main Frame """
        import pyorthanc
        import httpcore
        ttk.Frame.__init__(self, mainframe,  *args, **kwargs)
        self.orthanc = orthanc
        self.ITK_viewer = mainframe.ITKviewer
        logging.info(pyorthanc.find_studies(orthanc))
        self.label1 = tk.Label(self, text="Orthanc studies")
        self.label1.grid(row=0, column=0, sticky= tk.N + tk.W)

        self.tree = ttk.Treeview(self, columns=("Study ID", "Patient Name", "Description", "Patient ID", "Date", "Modalities"), show="headings")
        self.tree.grid(row=1, column=0, sticky= tk.N + tk.W + tk.E)
        self.tree.column("#0", width=0, stretch=False)  # Hide the first column
        # self.tree["columns"] = ("Study ID", "Patient Name", "Description", "Patient ID", "Date", "Modalities")
        
        for column in self.tree["columns"][:-1]:
            self.tree.column(column, stretch=False, width=100)  # Set a fixed width
            self.tree.heading(column, text=column, anchor=tk.W)
        
        self.tree.column("Modalities", stretch=True, width=100)  # Set a fixed width
        self.tree.heading("Modalities", text="Modalities", anchor=tk.W)

        self.tree_scrollbar_x = AutoScrollbar(self, orient='horizontal', command=self.tree.xview)
        self.tree.configure(xscrollcommand=self.tree_scrollbar_x.set)
        self.tree_scrollbar_x.grid(row=2, column=0, sticky=(tk.E, tk.W, tk.N))

        self.tree_scrollbar_y = AutoScrollbar(self, orient='vertical', command=self.tree.yview)
        self.tree.configure(yscrollcommand=self.tree_scrollbar_y.set)
        self.tree_scrollbar_y.grid(row=1, column=1, sticky=(tk.N, tk.S + tk.W))

        self.tree.bind("<Double-1>", self.selectItem)

        self.rowconfigure(1, weight=1)
        self.columnconfigure(0, weight=1)

        self.populate()

    def populate(self):
        patient_studies: List[pyorthanc.Study] = pyorthanc.find_studies(self.orthanc)
        
        self.tree.configure(height=len(patient_studies))

        for study in patient_studies:
            
            modalities = set( [series.modality for series in study.series] )
            
            try:
                uid = study.uid if hasattr(study, 'uid') else "No UID"
            except Exception as e:
                print(e)
                uid = "No UID"
            
            try:
                patient_identifier = study.patient_identifier if hasattr(study, 'patient_identifier') else "No patient identifier"
            except Exception as e:
                print(e)
                continue
            
            try:
                description = study.description if hasattr(study, 'description') else "No description"
            except Exception as e:
                print(e)
                description = "No description"
            
            try:
                patient_information = study.patient_information["PatientID"] if hasattr(study, 'patient_information') else "No patient information"
            except Exception as e:
                print(e)
                patient_information = "No patient information"
            
            try:
                date = study.date if hasattr(study, 'date') else "No date"
            except Exception as e:
                print(e)
                date = "No date"
                            
            self.tree.insert("", tk.END, text=uid, values=(uid, patient_identifier, description, patient_information, study.date, modalities))
            
    def selectItem(self, a):
        curItem = self.tree.focus()
        logging.info(self.tree.item(curItem))
        study = pyorthanc.find_studies(self.orthanc,query={"StudyInstanceUID":self.tree.item(curItem)["values"][0]})
        if len(study) == 0:
            logging.error(f"Could not find study with UID: {self.tree.item(curItem)['values'][0]}")
            return
        elif len(study) > 1:
            logging.error(f"Found multiple studies with UID: {self.tree.item(curItem)['values'][0]}")
            return
        study = study[0]
        instances_list = {}
        for serie in study.series:
            for instance in serie.instances:
                if serie.uid not in instances_list:
                    instances_list[serie.uid] = []
                max_retry = 5
                retry = 0
                while True:
                    try:
                        instances_list[serie.uid].append(instance.get_pydicom())
                        break
                    except httpcore.ReadTimeout:
                        logging.error(f"Read timeout, retrying, retry {retry}")
                        retry += 1
                        if retry > max_retry:
                            logging.error(f"Max retry reached, skipping instance")
                            break
                    except Exception as e:
                        logging.error(f"Could not get pydicom instance: {e}")
                        break

        self.ITK_viewer.DICOM_serie_manager.load_DICOM_serie(instance_list = instances_list)
        self.ITK_viewer.DICOM_serie_manager.reset_preview_frames()
        self.master.select(0)


class MainWindow(ttk.Notebook):
    """ Main window class """
    mainframe: tk.Tk
    threading: bool
    s: ttk.Style
    ITKviewer: ITKWindow

    def __init__(self, mainframe, threading = False, *args, **kwargs):
        """ Initialize the main Frame """
        ttk.Notebook.__init__(self, master=mainframe, height=100)
        self.mainframe = mainframe
        self.threading = threading
        self.master.title('ITK viewer')
        self.master.geometry('800x800')  # size of the main window

        self.s = ttk.Style()
        self.s.configure('Danger.TFrame', background='sky blue', borderwidth=5, relief='raised')
        self.ITKviewer = ITKWindow(self, threading=threading, style='Danger.TFrame', *args, **kwargs) # create ITK Frame

        self.add(self.ITKviewer, text="ITK viewer")
        self.grid(row=0, column=0, sticky= tk.N + tk.S + tk.E + tk.W)
    
        self.mainframe.rowconfigure(0, weight=1)
        self.mainframe.columnconfigure(0, weight=1)

    def add_orthanc(self, orthanc):
        self.orthanc: pyorthanc.Orthanc = orthanc
        self.orthanc_window = orthancWindow(self, orthanc, style='Danger.TFrame')
        self.add( self.orthanc_window, text="Orthanc")


    async def update(self) -> None:
        return super().update()
    
def donothing():
    """ Place holder callback"""


if __name__ == "__main__":        
    ITKapp = tk.Tk()
    app = MainWindow(ITKapp, threading=False)
    ITKapp.mainloop()
    # while True:
    #     try:
    #         app.update()
    #     except KeyboardInterrupt:
    #         break

