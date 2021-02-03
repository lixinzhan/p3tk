import os
import sys
import logging
import datetime
from typing import Sequence

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

class DICOMFORMAT():
    CT = 'CT'
    RS = 'RS'
    RD = 'RD'

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
        self.PlanImageSetMap = {}
        for planinfo in self.Patient.PlanList.Plan:
            self.PlanImageSetMap[planinfo.PlanID] = planinfo.PrimaryCTImageSetID

        # dicom preamble and prefix
        self.Preamble = b'0' * 128
        self.Prefix = 'DICM'

        # set them to -1 to make sure they are initialized
        # the values can be found in the Patient file
        self.ImageSetID = -1
        self.PlanID = -1
        
        # 'CT', 'RS' or 'RD'
        self.DICOMFORMAT = ''

        # plan files to be read in to
        self.ImgSetHeader = None
        self.ImgSetInfo = None
        self.ImageInfo = None
        self.PlanPatientSetup = None
        self.PlanInfo = None
        self.PlanPoints = None
        self.PlanROI = None
        self.PlanTrial = None

    def initializeForDicom(self, dst='CT', id=0):
        self.DICOMFORMAT = dst
        if dst == 'CT':
            self.ImageSetID = id
            self.PlanID = 0
            self.ImgSetHeader = readImageSetHeader(self.PFPath, self.ImageSetID)
            self.ImgSetInfo = readImageSetInfo(self.PFPath, self.ImageSetID)
            self.ImageInfo = readImageInfo(self.PFPath, self.ImageSetID).ImageInfo

            bitpix = self.ImgSetHeader.bitpix
            if   bitpix == 16: dtype = np.int16
            elif bitpix == 8:  dtype = np.int8
            elif bitpix == 32: dtype = np.int32
            else: dtype = np.short
            datafile = '%s/ImageSet_%s.img' % (self.PFPath, id)
            self.ImageData = np.fromfile(datafile, dtype) - 1000  # ***

        elif dst == 'RS' or dst == 'RD' or dst == 'RP':
            self.PlanID = id
            self.ImageSetID = self.PlanImageSetMap[id]
            self.ImgSetHeader = readImageSetHeader(self.PFPath, self.ImageSetID)
            self.ImgSetInfo = readImageSetInfo(self.PFPath, self.ImageSetID)
            self.ImageInfo = readImageInfo(self.PFPath, self.ImageSetID).ImageInfo
            self.PlanPatientSetup = readPlanPatientSetup(self.PFPath, self.PlanID)
            self.PlanInfo = readPlanInfo(self.PFPath, self.PlanID)
            self.PlanPoints = readPlanPoints(self.PFPath, self.PlanID)
            self.PlanROI = readPlanROI(self.PFPath, self.PlanID)
            self.PlanTrial = readPlanTrial(self.PFPath, self.PlanID)
        else:
            logging.error('Incorrect DICOM format: %s' % dst)
            print('Error: Incorrect DICOM format: %s' % dst)

        ## common UIDs
        self.SeriesUID = self.ImageInfo[0].SeriesUID
        self.StudyInstanceUID = self.ImageInfo[0].StudyInstanceUID
        self.FrameUID = self.ImageInfo[0].FrameUID

        if self.DICOMFORMAT == 'CT':
            self.ClassUID = ssopuids.CTImageStorage
        elif self.DICOMFORMAT == 'RS':
            self.ClassUID = ssopuids.RTStructureSetStorage
        elif self.DICOMFORMAT == 'RD':
            self.ClassUID = ssopuids.RTDoseStorage
        elif self.DICOMFORMAT == 'RP':
            self.ClassUID = ssopuids.RTPlanStorage

        # yyyy-mm-dd to yyyymmdd   
        img_set = self.Patient.ImageSetList.ImageSet[self.ImageSetID]
        self.ScanDate = self.ImgSetHeader.date.replace('-','')


    def _setSOPCommon(self, ds):
        ds.SpecificCharacterSet = 'ISO_IR 100'
        ds.is_little_endian = True
        ds.is_implicit_VR = False

        ds.SOPClassUID = self.ClassUID

    def _setFrameOfReference(self, ds):
        ds.FrameOfReferenceUID = self.FrameUID
        # ds.PositionReferenceIndicator = 'RF'  # not used, annotation purpose only

    def _setInstanceUID(self, ds, inst_uid):
        ds.SOPInstanceUID = inst_uid
        ds.InstanceCreationDate = self.ScanDate

    def _setStudyModule(self, ds):
        ds.StudyDate = self.ScanDate
        ds.StudyTime = ''
        ds.StudyInstanceUID = self.StudyInstanceUID
        ds.StudyID = self.ImgSetHeader.study_id

    def _setSeriesModule(self, ds):
        ds.SeriesDate = self.ScanDate
        ds.SeriesTime = ''
        ds.SeriesInstanceUID = self.SeriesUID
        ds.SeriesNumber = self.ImgSetHeader.exam_id
        ds.Modality = self.ImgSetHeader.modality
        ds.PatientPosition = self.ImgSetHeader.patient_position

    def _setEquipmentModule(self, ds):
        ds.Manufacturer = self.ImgSetHeader.manufacturer
        ds.ManufacturerModelName = self.ImgSetHeader.model
        ds.InstitutionName = dcmcommon.InstitutionName
        ds.InstitutionAddress = dcmcommon.InstitutionAddress
        ds.StationName = dcmcommon.StationName

    def _setGeneralCTImageModule(self, ds):
        # General Image Module
        ds.ImageType = r"ORIGINAL\PRIMARY\AXIAL"
        ds.AcquisitionDate = self.ScanDate
        ds.ContentDate = self.ScanDate
        ds.AcquisitionNumber = ''
        ds.InstanceNumber = ''
        ds.PatientOrientation = r'L\P'

        # CT Image Module
        ds.KVP = ''
        ds.TableHeight = 10.0*self.ImgSetHeader.couch_height
        ds.RotationDirection = 'CC'
        ds.ExposureTime = ''
        ds.XRayTubeCurrent = ''
        ds.GeneratorPower = ''
        ds.ConvolutionKernel = ''

        ds.SamplesPerPixel = 1
        ds.PhotometricInterpretation = "MONOCHROME2"
        ds.BitsAllocated = 16
        ds.BitsStored = 16
        ds.HighBit = 15
        ds.RescaleIntercept = 0
        ds.RescaleSlope = 1
        # ds.RescaleType = ''

    def _setImagePlanePixelModule(self, ds, index):
        ds.SliceThickness = self.ImgSetHeader.z_pixdim

        # Couch height considered here. Could be useful for coord trans??
        ds.ImagePositionPatient = [ 
            -10.0*self.ImgSetHeader.x_dim*self.ImgSetHeader.x_pixdim/2,
            -10.0*(self.ImgSetHeader.couch_height+self.ImgSetHeader.y_dim*self.ImgSetHeader.y_pixdim/2),
            -10.0*self.ImageInfo[index].TablePosition
            ]
        if self.ImgSetHeader.patient_position in ['HFP', 'FFP']:
            ds.ImageOrientationPatient = [-1.0,0.0,0.0,0.0,-1.0,-0.0]
        else: # if ds.PatientPosition in ['HFS', 'FFS']:
            ds.ImageOrientationPatient = [1.0,0.0,0.0,0.0,1.0,-0.0]
        ds.SliceLocation = 10.0*self.ImageInfo[index].CouchPos
        ds.PixelSpacing = [
            10.0*self.ImgSetHeader.x_pixdim, 
            10.0*self.ImgSetHeader.y_pixdim
            ]

        ds.Rows = self.ImgSetHeader.x_dim
        ds.Columns = self.ImgSetHeader.y_dim
        ds.PixelAspectRatio = r"1\1"            
        slicedata = self.ImageData[
            index*ds.Rows*ds.Columns:(index+1)*ds.Rows*ds.Columns
            ]
        ds.PixelRepresentation = 1
        ds.SmallestImagePixelValue = int(np.amin(slicedata))
        ds.LargestImagePixelValue  = int(np.amax(slicedata))
        ds.PixelData = slicedata.tobytes()

            
    def _setPatientModule(self, ds):
        ds.PatientName = '%s^%s^%s' % ( self.Patient.LastName, 
                                        self.Patient.FirstName, 
                                        self.Patient.MiddleName)
        ds.PatientID = self.Patient.MedicalRecordNumber
        ds.PatientBirthDate = self.Patient.DateOfBirth.replace('_','')
        ds.PatientSex = self.Patient.Gender[0]

    def _setVOILUTModule(self, ds):
        ds.WindowCenter = dcmcommon.WindowCenter
        ds.WindowWidth = dcmcommon.WindowWidth


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
        self.initializeForDicom('CT', imgsetid)
        datafile = '%s/ImageSet_%s.img' % (self.PFPath, imgsetid)
        if not os.path.isfile(datafile):
            print('No CT data file found: %s' % datafile)
            logging.error('No CT data file found: %s' % datafile)
            return False
        
        for i in range(self.ImgSetHeader.z_dim):
            file_meta = FileMetaDataset()
            file_meta.TransferSyntaxUID = pydicom.uid.ExplicitVRLittleEndian
            file_meta.MediaStorageSOPClassUID    = self.ClassUID
            file_meta.MediaStorageSOPInstanceUID = self.ImageInfo[i].InstanceUID

            ofname = '%s/CT.%s.dcm' % (self.OutPath, self.ImageInfo[i].InstanceUID)
            ds = FileDataset(ofname, {}, file_meta=file_meta, preamble=self.Preamble)

            self._setSOPCommon(ds)
            self._setPatientModule(ds)
            self._setFrameOfReference(ds)
            self._setStudyModule(ds)
            self._setSeriesModule(ds)
            self._setEquipmentModule(ds)
            self._setVOILUTModule(ds)
            self._setGeneralCTImageModule(ds)
            self._setImagePlanePixelModule(ds, i)
            self._setInstanceUID(ds, self.ImageInfo[i].InstanceUID)

            pydicom.dataset.validate_file_meta(ds.file_meta, enforce_standard=True)
            ds.save_as(ofname)
            logging.info('CT DICOM file saved: %s' % ofname)

        return True
        
    def _setFromPlanPoints(self, ds, planid=0):
        poi_point = readPlanPoints(self.PFPath, planid)

        count = 0
        for poi in poi_point.Poi:
            count += 1
            roi_contour = Dataset()
            sset_roi    = Dataset()
            rt_roi_obs  = Dataset()
            roi_contour.ReferencedROINumber = count
            sset_roi.ROINumber = count
            sset_roi.ROIName = poi.Name
            roi_contour.ContourSequence = pydicom.sequence.Sequence()
            sset_roi.ROIGenerationAlgorithm = 'SEMIAUTOMATIC'
            sset_roi.ReferencedFrameofReferencedUID = frameuid
            roi_contour.ROIDisplayColor = poi.Color


    def createDicomRS(self, planid=0):
        imgsetid = self.PlanImageSetMap[planid]
        img_info = readImageInfo(self.PFPath, imgsetid).ImageInfo
        plan_info = readPlanInfo(self.PFPath, planid)

        studyinstanceuid = img_info[0].StudyInstanceUID
        frameuid = img_info[0].FrameUID
        imageclassuid = img_info[0].ClassUID
        structclassuid = ssopuids.RTStructureSetStorage
        # imageinstanceuid: for each image slice
        imageseriesuid = img_info[0].SeriesUID
        structseriesuid = pydicom.uid.generate_uid()

        logging.info('Setting file meta for RS in Plan_%s...' % planid)
        file_meta = FileMetaDataset()
        file_meta.TransferSyntaxUID = pydicom.uid.ExplicitVRLittleEndian
        file_meta.MediaStorageSOPClassUID = structclassuid  # ssopuids.RTStructureSetStorage
        file_meta.MediaStorageSOPInstanceUID = pydicom.uid.generate_uid()

        ofname = '%s/RS.%s.dcm' % (self.OutPath, file_meta.MediaStorageSOPInstanceUID)
        ds = FileDataset(ofname, {}, file_meta=file_meta, preamble=self.Preamble)

        ds.is_little_endian = True
        ds.is_implicit_VR = False
        ds.SpecificCharacterSet = 'ISO_IR 100'

        ds.InstanceCreationDate = datetime.time.strftime("%Y%m%d")
        ds.InstanceCreationTime = datetime.time.strftime("%H%M%S")
        ds.SOPClassUID = ssopuids.RTStructureSetStorage
        ds.SOPInstanceUID = file_meta.MediaStorageSOPInstanceUID
        ds.Modality = 'RS'
        ds.Manufacturer = 'P3TK for PPlan'
        ds.Station = 'P3TK for PPlan'

        self._setFromPatientInfo(ds, planid)

        ds.StudyInstanceUID = studyinstanceuid
        ds.SeriesInstanceUID = structseriesuid

        ds.StructureSetLabel = plan_info.PlanName
        ds.StructureSetName  = plan_info.PlanName
        ds.RadiationOncologist = plan_info.Physician

        # ReferencedStudySequence
        ds.ReferencedStudySequence = pydicom.sequence.Sequence()
        refd_study = Dataset()
        refd_study.ReferencedSOPClassUID = '1.2.840.10008.3.1.2.3.2' #pydicom.uid.generate_uid()
        refd_study.ReferencedSOPInstanceUID =  ds.StudyInstanceUID   #pydicom.uid.generate_uid()
        ds.ReferencedStudySequence.append(refd_study)

        # ReferencedFrameOfReferenceSequence
        ds.ReferencedFrameOfReferenceSequence = pydicom.sequence.Sequence()
        refd_fref = Dataset()
        refd_fref.FrameOfReferenceUID = frameuid
        refd_fref.RTReferencedStudySequence = pydicom.sequence.Sequence()
        rt_refd_study = Dataset()
        rt_refd_study.ReferencedSOPClassUID = '1.2.840.10008.3.1.2.3.2'
        rt_refd_study.ReferencedSOPInstanceUID = studyinstanceuid
        rt_refd_study.RTReferencedSeriesSequence = pydicom.sequence.Sequence()
        rt_refd_series = Dataset()
        rt_refd_series.SeriesInstanceUID = imageseriesuid
        rt_refd_series.ContourImageSequence = pydicom.sequence.Sequence()
        for sliceinfo in img_info:
            contour_image = Dataset()
            contour_image.ReferencedSOPClassUID = sliceinfo.ClassUID
            contour_image.ReferencedSOPInstanceUID = sliceinfo.InstanceUID
            rt_refd_series.ContourImageSequence.append(contour_image)

        ds.ROIContourSequence = pydicom.sequence.Sequence()
        ds.StructureSetROISequence = pydicom.sequence.Sequence()
        ds.RTROIObservationsSequence = pydicom.sequence.Sequence()

        refd_fref.RTReferencedStudySequence.append(rt_refd_study)
        ds.ReferencedFrameOfReferenceSequence.append(refd_fref)


if __name__ == '__main__':
    prjpath = os.path.dirname(os.path.abspath(__file__))+'/../'

    FORMAT = "[%(asctime)s %(levelname)s - %(funcName)s] %(message)s"
    logging.basicConfig(format=FORMAT, filename=prjpath+'logs/test.log', level=logging.INFO)

    print('Start creating DICOM Files ...')
    pfDicom = PFDicom(prjpath+'examples/Patient_6204')
    pfDicom.createDicomCT(pfDicom.ImageSetIDs[0])
    print('DICOM ImageSet created.')
