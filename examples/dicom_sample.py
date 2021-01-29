# A sample DICOM file create program from the web.
# https://stackoverflow.com/questions/14350675/create-pydicom-file-from-numpy-array
#
# Notes for this sample code: 
# * Going through FileDataset constructor as PyDicom docs suggest was failing to create a valid header for me
# * validate_file_meta will create some missing elements in header for you (version)
# * You need to specify endianness and explicit/implicit VR twice :/
# * This method will allow you to create a valid volume as well as long as you update ImagePositionPatient and InstanceNumber for each slice accordingly
# * Make sure your numpy array is cast to data format that has same number of bits as your BitsStored
# * In order to fix this and write the meta into the dicom file, I needed to add enforce_standard=True to the save_as() call
#   But there is a comment saying should be 'write_like_original=False'

import pydicom
from pydicom.dataset import Dataset, FileDataset
from pydicom.uid import ExplicitVRLittleEndian
import pydicom._storage_sopclass_uids

image2d = image2d.astype(np.uint16)

print("Setting file meta information...")
# Populate required values for file meta information

meta = pydicom.Dataset()
meta.MediaStorageSOPClassUID = pydicom._storage_sopclass_uids.MRImageStorage
meta.MediaStorageSOPInstanceUID = pydicom.uid.generate_uid()
meta.TransferSyntaxUID = pydicom.uid.ExplicitVRLittleEndian  

ds = Dataset()
ds.file_meta = meta

ds.is_little_endian = True
ds.is_implicit_VR = False

ds.SOPClassUID = pydicom._storage_sopclass_uids.MRImageStorage
ds.PatientName = "Test^Firstname"
ds.PatientID = "123456"

ds.Modality = "MR"
ds.SeriesInstanceUID = pydicom.uid.generate_uid()
ds.StudyInstanceUID = pydicom.uid.generate_uid()
ds.FrameOfReferenceUID = pydicom.uid.generate_uid()

ds.BitsStored = 16
ds.BitsAllocated = 16
ds.SamplesPerPixel = 1
ds.HighBit = 15

ds.ImagesInAcquisition = "1"

ds.Rows = image2d.shape[0]
ds.Columns = image2d.shape[1]
ds.InstanceNumber = 1

ds.ImagePositionPatient = r"0\0\1"
ds.ImageOrientationPatient = r"1\0\0\0\-1\0"
ds.ImageType = r"ORIGINAL\PRIMARY\AXIAL"

ds.RescaleIntercept = "0"
ds.RescaleSlope = "1"
ds.PixelSpacing = r"1\1"
ds.PhotometricInterpretation = "MONOCHROME2"
ds.PixelRepresentation = 1

pydicom.dataset.validate_file_meta(ds.file_meta, enforce_standard=True)

print("Setting pixel data...")
ds.PixelData = image2d.tobytes()

ds.save_as(r"out.dcm")

