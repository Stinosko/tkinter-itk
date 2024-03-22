import SimpleITK as sitk
import numpy as np
import os
import pandas as pd
import cv2
import logging 
from PIL import Image

def read_image(image_path):
    """
    Read an image from a file path
    :param image_path: path to the image
    :return: the image
    """
    image = sitk.ReadImage(image)
    return image


def write_image(image, output_path):
    """
    Write an image to a file
    :param image: the image
    :param output_path: path to the output file
    """
    sitk.WriteImage(image, output_path)


def read_dicom_series(dicom_series_path):
    """
    Read a DICOM series from a folder
    :param dicom_series_path: path to the DICOM series
    :return: the DICOM series
    """
    reader = sitk.ImageSeriesReader()
    dicom_series = reader.GetGDCMSeriesFileNames(dicom_series_path)
    reader.SetFileNames(dicom_series)
    image = reader.Execute()
    return image


def overlay_segmentation(image, segmentation, alpha=0.5):
    """
    Overlay a segmentation on an image
    :param image: the image
    :param segmentation: the segmentation
    :param alpha: the transparency of the segmentation
    :return: the overlaid image
    """
    return sitk.LabelOverlay(image, segmentation, alpha)


def get_PIL_image_with_resolution(image, resolution):
    """
    Get a PIL image with a specific resolution
    :param image: the image
    :param resolution: the resolution
    :return: the PIL image
    """
    image.SetOrigin([0, 0]); image.SetDirection([1, 0, 0, 1])

    #lowest zoom level
    mask_real_size  = image.TransformPhysicalPointToIndex(resolution)

    ax_zoom_level = max(image.GetSize()[0] / mask_real_size[0], image.GetSize()[1] / mask_real_size[1])

    transform = sitk.Similarity2DTransform(image.GetDimension())
    
    transform.SetScale(ax_zoom_level)
    image  = sitk.Resample(image, resolution, transform, sitk.sitkLinear)

    image = isolate_region_based_on_segmentation(image.__copy__(), image.__copy__(), 0)

    return Image.fromarray(sitk.GetArrayFromImage(image).astype(np.uint8))


def get_stats_of_segmentation(segmentation_image: sitk.Image, input_image: sitk.Image):
    """
    Get statistics of a segmentation
    :param segmentation_image: the segmentation
    :param input_image: the original image
    :return: the statistics in a pandas dataframe
    """
    shape_stats = sitk.LabelShapeStatisticsImageFilter()
    shape_stats.ComputeOrientedBoundingBoxOn()
    shape_stats.Execute(segmentation_image)

    intensity_stats = sitk.LabelIntensityStatisticsImageFilter()
    intensity_stats.Execute(segmentation_image,input_image) 

    # Get highest number of segmentation label
    # Because some segmentation does not have all the labels
    # So shape_stats.GetNumberOfLabels() is not reliable
    amount = sitk.GetArrayFromImage(segmentation_image).max()

    stats_list = []

    for i in range(1, amount):
        if shape_stats.HasLabel(i):
                stats_list.append((shape_stats.GetPhysicalSize(i) * 0.001,
                                shape_stats.GetElongation(i),
                                shape_stats.GetFlatness(i),
                                shape_stats.GetOrientedBoundingBoxSize(i)[0],
                                shape_stats.GetOrientedBoundingBoxSize(i)[2],
                                intensity_stats.GetMean(i),
                                intensity_stats.GetStandardDeviation(i),
                                intensity_stats.GetSkewness(i), 
                                intensity_stats.GetMinimum(i),

                                intensity_stats.GetMaximum(i),))
        else:
                stats_list.append((0,0,0,0,0,0,0,0)) 

    cols=["Volume (ml)",
        "Elongation",
        "Flatness",
        "Oriented Bounding Box Minimum Size(cm)",
        "Oriented Bounding Box Maximum Size(cm)",
    "Intensity Mean",
    "Intensity Standard Deviation",
    "Intensity Skewness",
    "Intensity Minimum",
    "Intensity Maximum"]

    # Create the pandas data frame and display descriptive statistics.
    stats = pd.DataFrame(data=stats_list, columns=cols, index=range(1, amount))
    return stats


def get_label_outer_boundries(segmentation_image, label, x_buffer=0, y_buffer=0, z_buffer=0):
    """
    Get the outer boundaries of a label in a segmentation
    :param segmentation_image: the segmentation
    :param label: the label of the segmentation
    :param x_buffer: the buffer in the x direction
    :param y_buffer: the buffer in the y direction
    :param z_buffer: the buffer in the z direction
    :return: the outer boundaries
    """

    segmentation  = sitk.GetArrayFromImage(segmentation_image)
    no_liver_indices = np.where(segmentation != label)
    liver_indices = np.where(segmentation == label)

    segmentation[no_liver_indices] = 0
    x_min = np.min(np.where(segmentation == label)[0])
    x_max = np.max(np.where(segmentation == label)[0])
    y_min = np.min(np.where(segmentation == label)[1])
    y_max = np.max(np.where(segmentation == label)[1])
    z_min = np.min(np.where(segmentation == label)[2])
    z_max = np.max(np.where(segmentation == label)[2])

    x_min = x_min - x_buffer if x_min - x_buffer > 0 else 0
    x_max = x_max + x_buffer if x_max + x_buffer < segmentation.shape[0] else segmentation.shape[0]

    y_min = y_min - y_buffer if y_min - y_buffer > 0 else 0
    y_max = y_max + y_buffer if y_max + y_buffer < segmentation.shape[1] else segmentation.shape[1]

    z_min = z_min - z_buffer if z_min - z_buffer > 0 else 0
    z_max = z_max + z_buffer if z_max + z_buffer < segmentation.shape[2] else segmentation.shape[2]

    return x_min, x_max, y_min, y_max, z_min, z_max


def remove_background_based_on_segmentation(segmentation_image: sitk.Image, image: sitk.Image, label: int):
    """
    Remove the background of an image based on a segmentation
    :param segmentation_image: the segmentation
    :param image: the image
    :param label: the label of the segmentation
    :return: the image with the background removed
    """
    
    seg_array = sitk.GetArrayFromImage(segmentation_image)
    image_array = sitk.GetArrayFromImage(image)
    
    indices_not_present = np.where(seg_array != label)
    image_array[indices_not_present] = 0

    result_image = sitk.GetImageFromArray(image_array)
    result_image.CopyInformation(image)

    return result_image


def get_largest_connected_component(segmentation_image: sitk.Image, label: int):
    """
    Get the largest connected component of a segmentation
    :param segmentation_image: the segmentation
    :param label: the label of the segmentation
    :return: the largest connected component
    """
    # Get the largest connected component
    connected_component = sitk.ConnectedComponent(segmentation_image == label)
    relabeled, _, _ = sitk.RelabelComponent(connected_component)
    largest_connected_component = sitk.BinaryThreshold(relabeled, 1, 1)
    return largest_connected_component


def intensity_window_center_scale(image, window, level, min_out=0, max_out=255):
    intensity_transformer = sitk.IntensityWindowingImageFilter()
    intensity_transformer.SetOutputMaximum(max_out)
    intensity_transformer.SetOutputMinimum(min_out)
    intensity_transformer.SetWindowMaximum(int(level + window/2))
    intensity_transformer.SetWindowMinimum(int(level - window/2))


    return intensity_transformer.Execute(image)


def text_to_image(text, RGB = False, size_x = 512, slice_number = 0):
    """
    Write text on an image
    :param text: the text to write
    :param RGB: whether the image is RGB
    :param size_x: the width of the image
    :param slice_number: the slice number
    :return: the image with the text
    """
    size = [size_x, 40 + len(text.split('\n'))*40]
    
    if RGB:
        slice_array = np.zeros([size[1], size[0], 3], dtype=np.uint8)
    else:
        slice_array = np.zeros([size[1], size[0]], dtype=np.uint8)
    # Write the slice number on the slice
    
    color = (255, 255, 255) if RGB else (255, 255, 255)
    for i, line in enumerate(text.split('\n')):
        cv2.putText(slice_array, line, (10, 30 + i*40), cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2, cv2.LINE_AA)

    # cv2.putText(slice_array, f"Mean = {int(stats.iloc[4].loc['Intensity Mean'])}", (10, 110), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)
    # Convert the numpy array back to a SimpleITK image
    slice_with_number = sitk.GetImageFromArray(slice_array, isVector=RGB)

    # Stack the slices to create a 3D image
    seg_info_image = sitk.JoinSeries([slice_with_number, slice_with_number])
    # print(seg_info_image.GetPixelIDTypeAsString())
    return seg_info_image


def place_text_above_image(input_image, text, RGB = False):
    seg_info_image = text_to_image(text, RGB)

    # combine seg_info_image and input_image
    size = list(input_image.GetSize())
    
    
    if size[0] < seg_info_image.GetSize()[0]:
        size[0] = seg_info_image.GetSize()[0]

    size[1] = size[1] + seg_info_image.GetSize()[1]

        
    seg_info_image_array = sitk.GetArrayFromImage(seg_info_image)
    input_image_array = sitk.GetArrayFromImage(input_image)

    if RGB:
        comb_info_image = sitk.Image(size, sitk.sitkVectorUInt8)
    else:
        comb_info_image = sitk.Image(size, sitk.sitkUInt8)
    comb_info_image_array = sitk.GetArrayFromImage(comb_info_image)

    for i in range(0, comb_info_image_array.shape[0]):
        comb_info_image_array[i, 0:seg_info_image_array.shape[1], 0:seg_info_image_array.shape[2]] = seg_info_image_array[0, :, :]
        comb_info_image_array[i, seg_info_image_array.shape[1]:, :input_image_array.shape[2]] = input_image_array[i, :, :]


    comb_info_image = sitk.GetImageFromArray(comb_info_image_array)
    comb_info_image.SetSpacing(input_image.GetSpacing())
    comb_info_image.SetOrigin(input_image.GetOrigin())
    comb_info_image.SetDirection(input_image.GetDirection())

    return comb_info_image


def isolate_region_based_on_segmentation(image: sitk.Image, segmentation_image, label):
    """
    Isolate an image based on a segmentation
    :param image: the image
    :param segmentation: the segmentation
    :param label: the label of the segmentation
    :return: the isolated image
    """
    x_min, x_max, y_min, y_max, z_min, z_max = get_label_outer_boundries(segmentation_image, label, x_buffer=1, y_buffer=1, z_buffer=1)
    
    if image.GetDimension() == 2:
        isolated_image = image[y_min:y_max, x_min:x_max]
    elif image.GetDimension() == 3:
        isolated_image = image[z_min:z_max, y_min:y_max, x_min:x_max]
    else:
        logging.error(f"Image dimension is not 2 or 3: {image.GetDimension()}")
        raise ValueError("Image dimension is not 2 or 3")
    return isolated_image



def pydicom_2_sitk(pd_image):
    """Convert a pydicom image to a SimpleITK image"""
    # combine the pixel arrays
    array = np.empty((len(pd_image), pd_image[0].pixel_array.shape[0], pd_image[0].pixel_array.shape[1]))
    for i, item in enumerate( pd_image):
        array[i, :, :] = item.pixel_array
    # print(array.shape)
    array = array + pd_image[0].RescaleIntercept
    array[array < pd_image[0].RescaleIntercept] = pd_image[0].RescaleIntercept
    # convert to SimpleITK image
    image = sitk.GetImageFromArray(array)
    # set the origin, spacing and direction
    # print("origin: ", pd_image[0].get((0x0020, 0x0032)).value)
    image.SetOrigin(pd_image[0].get((0x0020, 0x0032)).value)
    spacing = pd_image[0].PixelSpacing
    slice_thickness = pd_image[0].get((0x0018, 0x0050)).value
    # print("spacing: ", spacing)
    # print("slice_thickness: ", slice_thickness)
    image.SetSpacing([spacing[0], spacing[1], slice_thickness])
    # print(pd_image[0].get((0x0020, 0x0037)).value)
    x, y = pd_image[0].get((0x0020, 0x0037)).value[0:3], pd_image[0].get((0x0020, 0x0037)).value[3:6]
    origin_start = pd_image[0].get((0x0020, 0x0032)).value
    origin_end = pd_image[-1].get((0x0020, 0x0032)).value
    z = np.array([origin_end[i] - origin_start[i] for i in range(3)])
    z = z / np.linalg.norm(z)
    image.SetDirection([x[0], y[0], z[0], x[1], y[1], z[1], x[2], y[2], z[2]])
    return image