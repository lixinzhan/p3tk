import os
import sys
import logging
import datetime

# from pftools.PFImgInfo import PFImgInfo
# from pftools.PFBackup import PFBackup
import pftools.common_dcm_settings as dcmcommon

from pftools.PFPatient import readPatient
from pftools.PFImgSetHeader import readImageSetHeader
from pftools.PFImgInfo import readImageInfo
from pftools.PFImgSetInfo import readImageSetInfo
from pftools.PFPlanInfo import readPlanInfo
from pftools.PFPlanPatientSetup import readPlanPatientSetup
from pftools.PFPlanPoints import readPlanPoints
from pftools.PFPlanROI import readPlanROI
from pftools.PFPlanTrial import readPlanTrial

import pydicom.uid
import pydicom.sequence
from pydicom.dataset import Dataset
from pydicom.dataset import FileDataset
from pydicom.dataset import FileMetaDataset
import pydicom._storage_sopclass_uids as ssopuids

import shutil
import numpy as np

class PFDicom():
    def __init__(self, pfpath, outpath='') -> None :
        logging.info('Start reading in Patient files from folder %s\n' % pfpath)
        self.Patient = readPatient(pfpath)

        # remember the input path and set the output path
        self.PFPath = pfpath
        self.OutPath = outpath
        if self.OutPath == '':
            self.OutPath = '%s/%s/' % (os.path.abspath(os.getcwd()), 
                            self.Patient.MedicalRecordNumber)
        if not os.path.exists(self.OutPath):
            os.makedirs(os.path.dirname(self.OutPath), exist_ok=True)

        self.NumberOfImageSets = len(self.Patient.ImageSetList.ImageSet)
        self.NumberOfPlans = len(self.Patient.PlanList.Plan)
        self.ImageSetIDs = []
        for id in range(self.NumberOfImageSets):
            self.ImageSetIDs.append(self.Patient.ImageSetList.ImageSet[id].ImageSetID)
        self.PlanIDs = []
        for id in range(self.NumberOfPlans):
            self.PlanIDs.append(self.Patient.PlanList.Plan[id].PlanID)

        # dicom preamble and prefix
        self.Preamble = b'0' * 128
        self.Prefix = 'DICM'

    def _setFromPatientInfo(self, ds, planid_imgsetid=0, dst=''):
        ds.PatientName = '%s^%s^%s' % ( self.Patient.LastName, 
                                        self.Patient.FirstName, 
                                        self.Patient.MiddleName)
        ds.PatientID = self.Patient.MedicalRecordNumber
        ds.PatientBirthDate = self.Patient.DateOfBirth.replace('_','')
        ds.PatientSex = self.Patient.Gender[0]

        if dst == 'RS':
            planid = planid_imgsetid
            ptplaninfo = self.Patient.PlanList.Plan[planid]
            ds.PrimaryCTImageSetID = ptplaninfo.PrimaryCTImageSetID
            ds.StudyID = str(self.Patient.ImageSetList.ImageSet[ds.PrimaryCTImageSetID].StudyID)

    def createDicomCT(self, imgsetid) -> None:
        ctpath = '%s/ImageSet_%s.DICOM/' % (self.PFPath, imgsetid)
        if os.path.exists(ctpath):
            logging.info('Existing DICOM ImageSet_%s. Copy to destination ...' % imgsetid)
            for ctfile in os.listdir(ctpath):
                ds_ct = pydicom.dcmread(ctpath+ctfile)
                instance_uid = ds_ct.SOPInstanceUID
                fsrc = ctpath+ctfile
                fdst = '%s/CT.%s.dcm' % (self.OutPath, instance_uid)
                shutil.copy2(fsrc, fdst)
            logging.info('ImageSet copy done.')
        else:
            logging.info('No existing DICOM ImageSet_%s. Generating ...' % imgsetid)
            self._createCTfromData(imgsetid)
            logging.info('DICOM ImageSet generated.')

    def _createCTfromData(self, imgsetid) -> bool:
        datafile = '%s/ImageSet_%s.img' % (self.PFPath, imgsetid)
        if not os.path.isfile(datafile):
            print('No CT data file found: %s' % datafile)
            logging.error('No CT data file found: %s' % datafile)
            return False
        
        imgset_header = readImageSetHeader(self.PFPath, imgsetid) # self.PFBackup.ImageSet[imgsetid].Header
        imgset_info = readImageSetInfo(self.PFPath, imgsetid)     # self.Patient.ImageSetList.ImageSet[imgsetid]
        img_info = readImageInfo(self.PFPath, imgsetid).ImageInfo # self.PFBackup.ImageSet[imgsetid].ImageInfoList.ImageInfo

        bitpix = imgset_header.bitpix
        if bitpix == 16: dtype = np.int16
        elif bitpix == 8: dtype = np.int8
        elif bitpix == 32: dtype = np.int32
        else: dtype = np.short
        x_dim = int(imgset_header.x_dim)
        y_dim = int(imgset_header.y_dim)
        z_dim = int(imgset_header.z_dim)
        alldata = np.fromfile(datafile, dtype) - 1000  # ***
        for i in range(z_dim):
            slicedata = alldata[i*x_dim*y_dim:(i+1)*x_dim*y_dim]

            file_meta = FileMetaDataset()
            file_meta.TransferSyntaxUID = pydicom.uid.ExplicitVRLittleEndian
            file_meta.MediaStorageSOPClassUID    = img_info[i].ClassUID
            file_meta.MediaStorageSOPInstanceUID = img_info[i].InstanceUID

            ofname = '%s/CT.%s.dcm' % (self.OutPath, img_info[i].InstanceUID)
            ds = FileDataset(ofname, {}, file_meta=file_meta, preamble=self.Preamble)

            ds.is_little_endian = True
            ds.is_implicit_VR = False

            ds.SpecificCharacterSet = 'ISO_IR 100'
            ds.ImageType = r"ORIGINAL\PRIMARY\AXIAL"
            ds.SOPClassUID = img_info[i].ClassUID
            ds.SOPInstanceUID = img_info[i].InstanceUID
            ds.SeriesInstanceUID = img_info[i].SeriesUID
            ds.StudyInstanceUID = img_info[i].StudyInstanceUID
            ds.FrameOfReferenceUID = img_info[i].FrameUID
            ds.Modality = imgset_header.modality
            ds.Manufacturer = imgset_header.manufacturer
            ds.ManufacturerModelName = imgset_header.model

            ds.InstitutionName = dcmcommon.InstitutionName
            ds.InstitutionAddress = dcmcommon.InstitutionAddress
            ds.StationName = dcmcommon.StationName
            ds.WindowCenter = dcmcommon.WindowCenter
            ds.WindowWidth = dcmcommon.WindowWidth

            date_scan = imgset_info.ScanTimeFromScanner.replace('-','') # yyyy-mm-dd to yyyymmdd
            ds.StudyDate = date_scan
            ds.SeriesDate = date_scan
            ds.AcquisitionDate = date_scan
            ds.ContentDate = date_scan
            ds.InstanceCreationDate = date_scan

            ds.StudyID = imgset_header.study_id
            ds.SeriesNumber = ''
            ds.AcquisitionNumber = ''
            ds.InstanceNumber = ''

            ds.BitsStored = 16
            ds.BitsAllocated = 16
            ds.SamplesPerPixel = 1
            ds.HighBit = 15
            
            self._setFromPatientInfo(ds, dst='CT')

            # ds.PatientName = '%s^%s^%s' % (self.PFBackup.Patient.LastName, 
            #                                 self.PFBackup.Patient.FirstName, 
            #                                 self.PFBackup.Patient.MiddleName)
            # ds.PatientID = self.PFBackup.Patient.MedicalRecordNumber
            # ds.PatientBirthDate = self.PFBackup.Patient.DateOfBirth.replace('_','')
            # ds.PatientSex = self.PFBackup.Patient.Gender[0]

            ds.RescaleIntercept = 0 # '-1024'
            ds.RescaleSlope = '1'
            ds.PixelRepresentation = 1
            ds.PhotometricInterpretation = "MONOCHROME2"
            ds.SamplesPerPixel = 1
            ds.PixelRepresentation = 1
            ds.SmallestImagePixelValue = int(np.amin(slicedata))
            ds.LargestImagePixelValue  = int(np.amax(slicedata))
            ds.PatientOrientation = r'L\P'
            ds.ImageOrientationPatient = r"1\0\0\0\-1\0"
            # Couch height considered here. Could be useful for coord trans??
            ds.ImagePositionPatient = [ -10*x_dim*imgset_header.x_pixdim/2,
                    -10*(imgset_header.couch_height+y_dim*imgset_header.y_pixdim/2),
                    -10*img_info[i].TablePosition]

            ds.TableHeight = imgset_header.couch_height*10.0
            ds.Rows = x_dim
            ds.Columns = y_dim
            ds.NumberOfSlices = z_dim
            ds.PixelSpacing = [imgset_header.x_pixdim*10.0, imgset_header.y_pixdim*10.0]
            ds.PixelAspectRatio = r"1\1"
            ds.SliceThickness = imgset_header.z_pixdim*10.0
            ds.SliceLocation = img_info[i].CouchPos * 10.0
            ds.InstanceNumber = img_info[i].SliceNumber
            ds.PatientPosition = imgset_header.patient_position
            if ds.PatientPosition in ['HFP', 'FFP']:
                ds.ImageOrientationPatient = [-1.0,0.0,0.0,0.0,-1.0,-0.0]
            else: # if ds.PatientPosition in ['HFS', 'FFS']:
                ds.ImageOrientationPatient = [1.0,0.0,0.0,0.0,1.0,-0.0]

            pydicom.dataset.validate_file_meta(ds.file_meta, enforce_standard=True)
            ds.PixelData = slicedata.tobytes()
            ds.save_as(ofname)
            logging.info('CT DICOM file saved: %s' % ofname)

        return True
        

    def createDicomRS(self, planid=0):
        logging.info('Setting file meta for RS in Plan_%s...' % planid)
        file_meta = FileMetaDataset()
        file_meta.TransferSyntaxUID = pydicom.uid.ExplicitVRLittleEndian
        file_meta.MediaStorageSOPClassUID = ssopuids.RTStructureSetStorage
        file_meta.MediaStorageSOPInstanceUID = pydicom.uid.generate_uid()

        ofname = '%s/RS.%s.dcm' % (self.OutPath, file_meta.MediaStorageSOPInstanceUID)
        ds = FileDataset(ofname, {}, file_meta=file_meta, preamble=self.Preamble)

        ds.is_little_endian = True
        ds.is_implicit_VR = False
        ds.SpecificCharacterSet = 'ISO_IR 100'

        ds.ReferencedStudySequence = pydicom.sequence.Sequence()

        ds.InstanceCreationDate = datetime.time.strftime("%Y%m%d")
        ds.InstanceCreationTime = datetime.time.strftime("%H%M%S")
        ds.SOPClassUID = ssopuids.RTStructureSetStorage
        ds.SOPInstanceUID = file_meta.MediaStorageSOPInstanceUID
        ds.Modality = 'RS'
        ds.Manufacturer = 'P3TK for PPlan'
        ds.Station = 'P3TK for PPlan'

        self._setFromPatientInfo(ds, planid)

        refd_study = Dataset()
        refd_study.ReferencedSOPClassUID = pydicom.uid.generate_uid()
        refd_study.ReferencedSOPInstanceUID = pydicom.uid.generate_uid()
        ds.ReferencedStudySequence.append(refd_study)

        ds.StudyInstanceUID = refd_study.ReferencedSOPInstanceUID
        ds.SeriesInstanceUID = pydicom.uid.generate_uid()

        plan_info = readPlanInfo(self.PFPath, planid)
        ds.StructureSetLabel = plan_info.PlanName
        ds.StructureSetName  = plan_info.PlanName
        ds.RadiationOncologist = plan_info.Physician

    

if __name__ == '__main__':
    prjpath = os.path.dirname(os.path.abspath(__file__))+'/../'

    FORMAT = "[%(asctime)s %(levelname)s - %(funcName)s] %(message)s"
    logging.basicConfig(format=FORMAT, filename=prjpath+'logs/test.log', level=logging.INFO)

    print('Start creating DICOM Files ...')
    pfDicom = PFDicom(prjpath+'examples/Patient_6204')
    pfDicom.createDicomCT(pfDicom.ImageSetIDs[0])
    print('DICOM ImageSet created.')
