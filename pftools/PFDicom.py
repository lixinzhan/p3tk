import os
import sys
import logging
from pftools.PFImgInfo import PFImgInfo
from pftools.PFBackup import PFBackup

import pydicom.uid
from pydicom.dataset import Dataset
from pydicom.dataset import FileDataset
from pydicom.dataset import FileMetaDataset
import pydicom._storage_sopclass_uids as ssopuids

import shutil
import numpy as np

class PFDicom():
    def __init__(self, pfpath, outpath='') -> None :
        logging.info('Start reading in Pinnacle backup files from folder %s\n' % pfpath)
        self.PFBackup = PFBackup(pfpath)
        logging.info('Reading Pinnacle backup files DONE!')

        # remember the input path and set the output path
        self.PFPath = pfpath
        self.OutPath = ''
        if outpath == '':
            self.OutPath = '%s/%s/' % (os.path.abspath(os.getcwd()), 
                            self.PFBackup.Patient.MedicalRecordNumber)
        else:
            self.OutPath = outpath

        # dicom preamble and prefix
        self.Preamble = b'0' * 128
        self.Prefix = 'DICM'

    def createDicomCT(self):
        logging.info('Setting file meta information ...')
        self.FileMeta = FileMetaDataset()

        # Explicit VR Little Endian '1.2.840.10008.1.2.1'
        self.FileMeta.TransferSyntaxUID = pydicom.uid.ExplicitVRLittleEndian

        # CT Image Storage '1.2.840.10008.5.1.4.1.1.2'
        self.FileMeta.MediaStorageSOPClassUID = ssopuids.CTImageStorage 
        self.FileMeta.MediaStorageSOPInstanceUID = pydicom.uid.generate_uid()
        self.FileMeta.ImplementationClassUID = pydicom.uid.generate_uid()

        for imgSet in self.PFBackup.ImageSet:
            ctpath = '%s/ImageSet_%s.DICOM/' % (self.PFPath, imgSet.ImageSetID)
            if os.path.exists(ctpath):
                for ctfile in os.listdir(ctpath):
                    ds_ct = pydicom.dcmread(ctpath+ctfile)
                    instance_uid = ds_ct.SOPInstanceUID
                    fsrc = ctpath+ctfile
                    fdst = '%s/CT.%s.dcm' % (self.OutPath, instance_uid)
                    shutil.copy2(fsrc, fdst)
            else:
                self._createCTfromData(imgSet.ImageSetID)

    def _createCTfromData(self, imgsetid) -> bool:
        datafile = '%s/ImageSet_%s.img' % (self.PFPath, imgsetid)
        if not os.path.isfile(datafile):
            print('No CT Data found!')
            return False
        
        img_header = self.PFBackup.ImageSet[imgsetid].Header
        imgset_info = self.PFBackup.Patient.ImageSetList.ImageSet[imgsetid]
        img_info = self.PFBackup.ImageSet[imgsetid].ImageInfoList.ImageInfo

        bitpix = self.PFBackup.ImageSet[imgsetid].Header.bitpix
        if bitpix == 16: dtype = np.uint16
        elif bitpix == 8: dtype = np.uint8
        elif bitpix == 32: dtype = np.uint32
        else: dtype = np.short
        x_dim = int(self.PFBackup.ImageSet[imgsetid].Header.x_dim)
        y_dim = int(self.PFBackup.ImageSet[imgsetid].Header.y_dim)
        z_dim = int(self.PFBackup.ImageSet[imgsetid].Header.z_dim)
        alldata = np.fromfile(datafile, dtype)
        slicelist = []
        for i in range(z_dim):
            slicedata = alldata[i*x_dim*y_dim:(i+1)*x_dim*y_dim]
            #slicelist.append(slicedata)

            file_meta = FileMetaDataset()
            file_meta.TransferSyntaxUID = pydicom.uid.ExplicitVRLittleEndian
            file_meta.MediaStorageSOPClassUID = img_info[i].ClassUID
            file_meta.MediaStorageSOPInstanceUID = img_info[i].InstanceUID

            ofname = '%s/CT.%s.dcm' % (self.OutPath, img_info[i].InstanceUID)
            ds = FileDataset(ofname, {}, file_meta=file_meta, preamble=self.Preamble)

            ds.is_little_endian = True
            ds.is_implicit_VR = False

            ds.SpecificCharacterSet = 'ISO_IR 100'
            ds.ImageType = r"ORIGINAL\PRIMARY\AXIAL"
            ds.ImagePositionPatient = r"0\0\1"
            ds.ImageOrientationPatient = r"1\0\0\0\-1\0"
            ds.SOPClassUID = img_info[i].ClassUID
            ds.SOPInstanceUID = img_info[i].InstanceUID
            ds.SeriesInstanceUID = img_info[i].SeriesUID
            ds.StudyInstanceUID = img_info[i].StudyInstanceUID
            ds.FrameOfReferenceUID = img_info[i].FrameUID
            ds.Modality = img_header.modality
            ds.Manufacturer = img_header.manufacturer

            date_scan = imgset_info.ScanTimeFromScanner.replace('-','') # yyyy-mm-dd to yyyymmdd
            ds.StudyDate = date_scan
            ds.SeriesDate = date_scan
            ds.AcquisitionDate = date_scan
            ds.ContentDate = date_scan

            ds.BitsStored = 16
            ds.BitsAllocated = 16
            ds.SamplesPerPixel = 1
            ds.HighBit = 15
            
            ds.PatientName = '%s^%s^%s' % (self.PFBackup.Patient.LastName, 
                                            self.PFBackup.Patient.FirstName, 
                                            self.PFBackup.Patient.MiddleName)
            ds.PatientID = self.PFBackup.Patient.MedicalRecordNumber
            ds.PatientBirthDate = self.PFBackup.Patient.DateOfBirth.replace('_','')

            ds.RescaleIntercept = '-1024'
            ds.RescaleSlope = '1'
            ds.PixelRepresentation = 1
            ds.PhotometricInterpretation = "MONOCHROME2"
            ds.SamplesPerPixel = 1
            # ds.ImagesInAcquisition = '1'
            # ds.PixelRepresentation = 1

            ds.PixelSpacing = [img_header.x_pixdim*10.0, img_header.y_pixdim*10.0]
            ds.SliceThickness = img_header.z_pixdim*10.0
            ds.Rows = x_dim
            ds.Columns = y_dim
            ds.NumberOfSlices = z_dim
            ds.SliceLocation = img_info[i].TablePosition * 10.0
            ds.InstanceNumber = img_info[i].SliceNumber
            ds.PatientPosition = img_header.patient_position
            if ds.PatientPosition in ['HFP', 'FFP']:
                ds.ImageOrientationPatient = [-1.0,0.0,0.0,0.0,-1.0,-0.0]
            else: # if ds.PatientPosition in ['HFS', 'FFS']:
                ds.ImageOrientationPatient = [1.0,0.0,0.0,0.0,1.0,-0.0]

            pydicom.dataset.validate_file_meta(ds.file_meta, enforce_standard=True)
            ds.PixelData = slicedata.tobytes()
            ds.save_as(ofname)
        

if __name__ == '__main__':
    prjpath = os.path.dirname(os.path.abspath(__file__))+'/../'

    FORMAT = "[%(asctime)s %(levelname)s - %(funcName)s] %(message)s"
    logging.basicConfig(format=FORMAT, filename=prjpath+'logs/test.log', level=logging.INFO)

    print('Start creating DICOM Files ...')
    pfDicom = PFDicom(prjpath+'examples/Patient_6204')
    pfDicom.createDicomCT()
