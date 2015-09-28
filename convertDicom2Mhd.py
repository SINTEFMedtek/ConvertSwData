import datetime
import dicom
from dicom.filereader import InvalidDicomError
#import numpy as np
import logging
import os
import re

logger = logging.getLogger('Convert data')
        
def readDicom(dicomFile):
    try:
        return dicom.read_file(dicomFile)
    except InvalidDicomError:
        return None
 
def writeMhdRaw(FolderPathOut, dataset):
    Frames_key = (0x0028, 0x0008)
    Rows_key = (0x0028, 0x0010)
    Columns_key = (0x0028, 0x0011)
    ElementSpacing_key = (0x0028, 0x0030)
    ElementSpacingZ_key = (0x0018, 0x0050)
    Modality_key = (0x0008, 0x0060)
    WindowLevel_key = (0x0028, 0x1050)
    WindowWidth_key = (0X0028, 0X1051)
    ImageOrientationPatient_key = (0x0020, 0x0037)
    ImagePositionPatient_key = (0x0020, 0x0032)
    SeriesDescription_key = (0x0008, 0x103e)
    AcqDate_key = (0x8,0x20)
    
    buffer = 'ObjectType = Image'+ os.linesep

    numberOfFrames = _rec_traverse_dataset(dataset, look_for_tag=Frames_key)
    numberOfRows = _rec_traverse_dataset(dataset, look_for_tag=Rows_key)
    numberOfColumns = _rec_traverse_dataset(dataset, look_for_tag=Columns_key)

    if numberOfFrames == 0 and numberOfRows*numberOfColumns > 0:
        numberOfFrames = 1
    if numberOfFrames == 0:
        logger.error( 'Found no frames, skipping..')
        return None
    elif numberOfFrames > 1:
         buffer += 'NDims = 3' + os.linesep
    else:
         buffer += 'NDims = 2' + os.linesep

    buffer += 'BinaryData = True' + os.linesep
    buffer += 'BinaryDataByteOrderMSB = False' + os.linesep
    buffer += 'CompressedData = False' + os.linesep
    buffer += 'CenterOfRotation = 0 0 0' + os.linesep

    val1 = _rec_traverse_dataset(dataset, look_for_tag=ElementSpacing_key)
    val2 = _rec_traverse_dataset(dataset, look_for_tag=ElementSpacingZ_key)
    if val1 and val2:
        buffer += 'ElementSpacing =' + str(val1[0]) + str(" ") + str(val1[1]) + str(" ") + str(val2) + os.linesep
    else:
        logger.error("Could not find ElementSpacing, assuming [1 1 1]")
        buffer += 'ElementSpacing = 1 1 1' + os.linesep

    buffer += 'DimSize = ' + str(numberOfColumns) + str(" ") + str(numberOfRows) + str(" ") + str(numberOfFrames)+ os.linesep
    buffer += 'AnatomicalOrientation = ???'+ os.linesep

    if dataset.pixel_array.dtype == 'uint8':
        buffer += 'ElementType = MET_UCHAR'+ os.linesep
    elif dataset.pixel_array.dtype == 'int16':
        buffer += 'ElementType = MET_SHORT'+ os.linesep
    elif dataset.pixel_array.dtype == 'float32':
        buffer += 'ElementType = MET_FLOAT'+ os.linesep
    elif dataset.pixel_array.dtype == 'double':
        buffer += 'ElementType = MET_DOUBLE'+ os.linesep
    elif dataset.pixel_array.dtype == 'int8':
        buffer += 'ElementType = MET_CHAR'+ os.linesep
    elif dataset.pixel_array.dtype == 'uint16':
        buffer += 'ElementType = MET_USHORT'+ os.linesep
    elif dataset.pixel_array.dtype == 'int32':
        buffer += 'ElementType = MET_INT'+ os.linesep
    elif dataset.pixel_array.dtype == 'uint32':
        buffer += 'ElementType = MET_UINT'+ os.linesep
    else:
        logger.error( "Unsupport element type", dataset.pixel_array.dtype)
        return None

    val = _rec_traverse_dataset(dataset, look_for_tag=Modality_key)
    if val:
        buffer += 'Modality = '+ str(val)+ os.linesep
    else:
        logger.info( "Could not find modality, assuming US")
        buffer += 'Modality = ' + 'US'+ os.linesep

    val = _rec_traverse_dataset(dataset, look_for_tag=WindowLevel_key)
    if val:
        buffer += 'WindowLevel = ' + str(val)+ os.linesep

    val = _rec_traverse_dataset(dataset, look_for_tag=WindowWidth_key)
    if val:
        buffer += 'WindowWidth = ' + str(val)+ os.linesep
    buffer += 'Creator = pydicom2mhd-'+datetime.datetime.now().strftime("%Y-%m-%d_%H:%M:%S")+ os.linesep

    val = _rec_traverse_dataset(dataset, look_for_tag=ImageOrientationPatient_key)
    if val:
        e_x = [float(k) for k in val[0:3]]
        e_y = [float(k) for k in val[3:6]]
        e_z = cross(e_x, e_y)
        val.extend(e_z)
        buffer += 'TransformMatrix = ' + _convertNumbersToString(val)+ os.linesep
    else:
        logger.info( "Could not find TransformMatrix, assuming identity")
        buffer += 'TransformMatrix = 1 0 0 0 1 0 0 0 1'+ os.linesep

    val = _rec_traverse_dataset(dataset, look_for_tag=ImagePositionPatient_key)
    if val:
        buffer += 'Offset = ' + _convertNumbersToString(val)+ os.linesep
    else:
        logger.info( "Could not find Offset, assuming [0 0 0]")
        buffer += 'Offset = 0 0 0'+ os.linesep

    SeriesDescription = _rec_traverse_dataset(dataset, look_for_tag=SeriesDescription_key)
    if SeriesDescription:
        baseName = str(SeriesDescription).replace(' ', '_')
    else:
        acq_date = _rec_traverse_dataset(dataset, look_for_tag=AcqDate_key)
        if acq_date:
            baseName = str(acq_date).replace(' ', '_')
        else:
            baseName = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
                    
    baseName = re.sub('[^\w\-_\. ]', '_', baseName)
    filePathOut = os.path.join(FolderPathOut, baseName + '.mhd')
    k=1
    while os.path.exists(filePathOut):
        k = k+1
        filePathOut = os.path.join(FolderPathOut, baseName+"_"+str(k) + '.mhd')

 
    buffer += 'ElementDataFile = ' + os.path.basename(filePathOut).replace('.mhd', '.raw')
   
    mhd_file = open(filePathOut, 'w')
    mhd_file.write(buffer)
    mhd_file.close()
       
    _writeRaw(filePathOut.replace('.mhd', '.raw'), dataset.pixel_array)

def _writeRaw(filePathOut, data):
    f = open(filePathOut, 'wb')
    f.write(data)
    f.close()

def _rec_traverse_dataset(ds, look_for_tag=None):
    ''' Recursively traverse a Dataset and look for tag. '''
    if look_for_tag in ds.keys():
        return ds[look_for_tag].value
    for key in ds.keys():
        val = ds[key].value
        if type(val) is dicom.sequence.Sequence:
            for i in range(0, len(val)):
                sub_ds = val[i]
                res = _rec_traverse_dataset(sub_ds, look_for_tag=look_for_tag)
                if res:
                    return res
    return None


def _convertNumbersToString(num):
    return " ".join("%0.5f" % (e,) for e in num)


def cross(a, b):
    c = [a[1]*b[2] - a[2]*b[1],
         a[2]*b[0] - a[0]*b[2],
         a[0]*b[1] - a[1]*b[0]]

    return c