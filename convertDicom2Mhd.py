import datetime
import dicom
from dicom.filereader import InvalidDicomError
import numpy as np
import logging
import os
import re
from sys import byteorder
import zlib
sys_is_little_endian = (byteorder == 'little')

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
    AcqTime_key = (0x8, 0x30)

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


    need_byteswap = (dataset.is_little_endian != sys_is_little_endian)

    # Make NumPy format code, e.g. "uint16", "int32" etc
    # from two pieces of info:
    #    self.PixelRepresentation -- 0 for unsigned, 1 for signed;
    #    self.BitsAllocated -- 8, 16, or 32
    format_str = '%sint%d' % (('u', '')[dataset.PixelRepresentation],
                              dataset.BitsAllocated)
    try:
        numpy_format = np.dtype(format_str)
    except TypeError:
        msg = ("Data type not understood by NumPy: "
               "format='%s', PixelRepresentation=%d, BitsAllocated=%d")
        raise TypeError(msg % (numpy_format, dataset.PixelRepresentation,
                        dataset.BitsAllocated))

    # copy from pydicom dataset _pixel_data_numpy
    # Have correct Numpy format, so create the NumPy array
    arr = np.fromstring(dataset.PixelData, numpy_format)

    if need_byteswap:
        arr.byteswap(True)  # True means swap in-place, don't make a new copy

    if len(arr) ~= dataset.NumberOfFrames*dataset.Rows*dataset.Columns:
        logger.error("Wrong number of elements in dataset")
        arr = arr[0:(dataset.NumberOfFrames*dataset.Rows*dataset.Columns)]
    arr = arr.reshape(dataset.NumberOfFrames, dataset.Rows, dataset.Columns)
    data = arr

    if data.dtype == 'uint8':
        buffer += 'ElementType = MET_UCHAR'+ os.linesep
    elif data.dtype == 'int16':
        buffer += 'ElementType = MET_SHORT'+ os.linesep
    elif data.dtype == 'float32':
        buffer += 'ElementType = MET_FLOAT'+ os.linesep
    elif data.dtype == 'double':
        buffer += 'ElementType = MET_DOUBLE'+ os.linesep
    elif data.dtype == 'int8':
        buffer += 'ElementType = MET_CHAR'+ os.linesep
    elif data.dtype == 'uint16':
        buffer += 'ElementType = MET_USHORT'+ os.linesep
    elif data.dtype == 'int32':
        buffer += 'ElementType = MET_INT'+ os.linesep
    elif data.dtype == 'uint32':
        buffer += 'ElementType = MET_UINT'+ os.linesep
    else:
        logger.error( "Unsupport element type", data.dtype)
        return None

    modality = _rec_traverse_dataset(dataset, look_for_tag=Modality_key)
    if modality:
        buffer += 'Modality = '+ str(modality)+ os.linesep
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

        
    val = _rec_traverse_dataset(dataset, look_for_tag=SeriesDescription_key)
    if val:
        modality = val.replace(' ', '_')
        modality = re.sub('[^\w\-_\. ]', '_', modality)
        
    acq_date = _rec_traverse_dataset(dataset, look_for_tag=AcqDate_key)
    acq_date = str(acq_date).replace(' ', '_')
    acq_date = re.sub('[^\w\-_\. ]', '_', acq_date)
    baseName = acq_date
    
    baseName = baseName+"_"+ str(modality)

    filePathOut = os.path.join(FolderPathOut, baseName +"_"+str(1)+ '.mhd')
    k=1
    while os.path.exists(filePathOut):
        k = k+1
        filePathOut = os.path.join(FolderPathOut, baseName+ "_"+str(k) + '.mhd')
 
    buffer += 'ElementDataFile = ' + os.path.basename(filePathOut).replace('.mhd', '.raw')
   
    mhd_file = open(filePathOut, 'w')
    mhd_file.write(buffer)
    mhd_file.close()

    _writeRaw(filePathOut.replace('.mhd', '.raw'), data)
   
    return acq_date

def _writeRaw(filePathOut, data, compress=True):
    f = open(filePathOut, 'wb')
    if compress:
        data = zlib.compress(data)
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