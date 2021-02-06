import os
import sys
import logging
import datetime
from typing import List, Sequence

from numpy.core.records import _deprecate_shape_0_as_None

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
import pydicom._uid_dict as uid_dict

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
        self.PlanImageSetMap = {}
        for planinfo in self.Patient.PlanList.Plan:
            self.PlanImageSetMap[planinfo.PlanID] = planinfo.PrimaryCTImageSetID

        # dicom preamble and prefix
        self.Preamble = b'\x00' * 128
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

    def _initializeForDicom(self, dst='CT', id=0):
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
        # self.SeriesUID = self.ImageInfo[0].SeriesUID
        # self.StudyInstanceUID = self.ImageInfo[0].StudyInstanceUID
        # self.FrameUID = self.ImageInfo[0].FrameUID

        self.TransferSyntaxUID = pydicom.uid.ExplicitVRLittleEndian

        # Entropy src based SOPInstanceUID for CT, RS, RP, and RD
        self.CTSOPInstanceUID = [] #pydicom.uid.generate_uid() # one for each image
        for i in range(self.ImgSetInfo.NumberOfImages):
            entropy_src = [ self.Patient.MedicalRecordNumber, str(self.ImageSetID), 
                            str(self.ImageInfo[i].SliceNumber), 'CT']
            self.CTSOPInstanceUID.append(
                pydicom.uid.generate_uid(entropy_srcs=entropy_src)
                )
        entropy_src = [ self.Patient.MedicalRecordNumber, str(self.ImageSetID), 
                        str(self.PlanID), 'RS']
        self.RSSOPInstanceUID = pydicom.uid.generate_uid(entropy_srcs=entropy_src)
        entropy_src = [ self.Patient.MedicalRecordNumber, str(self.ImageSetID), 
                        str(self.PlanID), 'RP']
        self.RPSOPInstanceUID = pydicom.uid.generate_uid(entropy_srcs=entropy_src)
        entropy_src = [ self.Patient.MedicalRecordNumber, str(self.ImageSetID), 
                        str(self.PlanID), 'RD']
        self.RDSOPInstanceUID = pydicom.uid.generate_uid(entropy_srcs=entropy_src)

        if self.DICOMFORMAT == 'CT':
            self.StorageSOPClassUID = ssopuids.CTImageStorage
            self.StorageSOPInstanceUID = self.CTSOPInstanceUID
        elif self.DICOMFORMAT == 'RS':
            self.StorageSOPClassUID = ssopuids.RTStructureSetStorage
            self.StorageSOPInstanceUID = self.RSSOPInstanceUID
        elif self.DICOMFORMAT == 'RD':
            self.StorageSOPClassUID = ssopuids.RTDoseStorage
            self.StorageSOPInstanceUID = self.RDSOPInstanceUID
        elif self.DICOMFORMAT == 'RP':
            self.StorageSOPClassUID = ssopuids.RTPlanStorage
            self.StorageSOPInstanceUID = self.RPSOPInstanceUID
        self.SOPClassUID = self.StorageSOPClassUID
        self.SOPInstanceUID = self.StorageSOPInstanceUID

        self.CTSOPClassUID = ssopuids.CTImageStorage
        self.RSSOPClassUID = ssopuids.RTStructureSetStorage
        self.RPSOPClassUID = ssopuids.RTPlanStorage
        self.RDSOPClassUID = ssopuids.RTDoseStorage

        self.FrameOfReferenceUID = pydicom.uid.generate_uid()

        self.StudySOPClassUID = self.SOPClassUID
        self.StudySOPInstanceUID = pydicom.uid.generate_uid()

        # self.SeriesSOPClassUID = ssopuids.CTImageStorage
        self.SeriesSOPInstanceUID = pydicom.uid.generate_uid()

        #print('2. StorageSOPClassUID: %s' % self.StorageSOPClassUID)
        #print('DICOMFORMAT: %s and uid %s' % (self.DICOMFORMAT, ssopuids.RTStructureSetStorage))

        # self.ClassUID = self.StorageSOPClassUID  # temp
        # self.FrameUID = self.FrameOfReferenceUID # temp
        # self.StudyInstanceUID = self.StorageSOPInstanceUID  # temp
        # self.SeriesUID = self.SeriesSOPClassUID  # temp

        # yyyy-mm-dd to yyyymmdd   
        img_set = self.Patient.ImageSetList.ImageSet[self.ImageSetID]
        self.ScanDate = self.ImgSetHeader.date.replace('-','')

        x0 = self.ImgSetHeader.x_start
        y0 = self.ImgSetHeader.y_start
        z0 = self.ImgSetHeader.z_start
        nx = self.ImgSetHeader.x_dim
        ny = self.ImgSetHeader.y_dim
        nz = self.ImgSetHeader.z_dim
        dx = self.ImgSetHeader.x_pixdim
        dy = self.ImgSetHeader.y_pixdim
        dz = self.ImgSetHeader.z_pixdim
        yc = self.ImgSetHeader.couch_height + dy   # couch height
        self.Xshift = 0 # x0 + (nx-1)*dx/2.0
        self.Yshift = y0 - yc + (ny-1)*dy/2.0
        self.Zshift = 0 # -(z0 + (nz-1)*dz/2.0)

    def transCoord(self, clist=[]) -> List:
        trans = []
        for i in range(len(clist)):
            if i%3 == 0: # x
                xyz = clist[i]
            elif i%3 == 1: # y
                # ystart = self.ImgSetHeader.y_start
                # y_dim = self.ImgSetHeader.y_dim
                # ypixdim = self.ImgSetHeader.y_pixdim
                # y = 2.0*ystart-clist[i]+2.0*(y_dim-1)*ypixdim
                xyz = -(clist[i] - self.Yshift)
            else: # i%3 == 2: # z
                xyz = -clist[i]
            trans.append('%6.2f' % (xyz*10.0))
        return trans


    def _setSOPCommon(self, ds):
        ds.SpecificCharacterSet = 'ISO_IR 100'
        ds.is_little_endian = True
        ds.is_implicit_VR = False
        ds.SOPClassUID = self.SOPClassUID

    def _setFrameOfReference(self, ds):
        ds.FrameOfReferenceUID = self.FrameOfReferenceUID
        # ds.PositionReferenceIndicator = 'RF'  # not used, annotation purpose only

    def _setInstanceUID(self, ds, inst_uid=''):
        ds.SOPInstanceUID = inst_uid
        if self.DICOMFORMAT == 'CT':
            ds.InstanceCreationDate = self.ScanDate
        elif self.DICOMFORMAT == 'RS' or self.DICOMFORMAT == 'RD':
            ds.InstanceCreationDate = self.PlanPatientSetup.ObjectVersion.WriteTimeStamp[:10].replace('-','')

    def _getReferencedStudySequence(self):
        seq = pydicom.sequence.Sequence()
        ref_study = Dataset()
        ref_study.ReferencedSOPClassUID = self.CTSOPClassUID
        ref_study.ReferencedSOPInstanceUID = self.StudySOPInstanceUID

    def _setStudyModule(self, ds):
        ds.StudyDate = self.ScanDate
        ds.StudyTime = ''
        ds.StudyInstanceUID = self.StudySOPInstanceUID
        ds.StudyID = self.ImgSetHeader.study_id
        if self.DICOMFORMAT != 'CT':
            ds.ReferencedStudySequence = self._getReferencedStudySequence()

    def _setSeriesModule(self, ds):
        # Series Number (0020,0011) is a human readable numeric label, which may be empty 
        # and is not unique within any defined scope; it is required to have the same value 
        # for all instances that have the same Series Instance UID (0020,000E) 
        # (this is true of all attributes for the same "entity"), but there is no requirement 
        # that it be different for different series (though this is often the case for 
        # different series in the same study, especially if produced by the same equipment) 
        ds.SeriesDate = self.ScanDate
        ds.SeriesTime = ''
        ds.SeriesInstanceUID = self.SeriesSOPInstanceUID
        ds.SeriesNumber = self.ImgSetHeader.exam_id
        if self.DICOMFORMAT == 'CT':
            ds.Modality = 'CT'
        elif self.DICOMFORMAT == 'RS':
            ds.Modality = 'RTSTRUCT'
        elif self.DICOMFORMAT == 'RP':
            ds.Modality = 'RTPLAN'
        elif self.DICOMFORMAT == 'RD':
            self.Modality = 'RTDOSE'
        else:
            ds.Modality = self.DICOMFORMAT
        ds.PatientPosition = self.ImgSetHeader.patient_position
            

    def _setEquipmentModule(self, ds):
        if self.DICOMFORMAT == 'CT':
            ds.Manufacturer = self.ImgSetHeader.manufacturer
            ds.ManufacturerModelName = self.ImgSetHeader.model
        else:
            ds.Manufacturer = 'P3TK'
            # ds.ManufactureModelName = self.DICOMFORMAT
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
        ds.PixelSpacing = [ 10.0*self.ImgSetHeader.x_pixdim, 
                            10.0*self.ImgSetHeader.y_pixdim]

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
        # ctpath = '%s/ImageSet_%s.DICOM/' % (self.PFPath, imgsetid)
        # if os.path.exists(ctpath):
        #     logging.info('Existing DICOM ImageSet_%s. Copy to destination ...' % imgsetid)
        #     for ctfile in os.listdir(ctpath):
        #         ds_ct = pydicom.dcmread(ctpath+ctfile)
        #         instance_uid = ds_ct.SOPInstanceUID
        #         fsrc = ctpath+ctfile
        #         fdst = '%s/CT.%s.dcm' % (self.OutPath, instance_uid)
        #         shutil.copy2(fsrc, fdst)
        #     logging.info('ImageSet copy done.')
        # else:
        #     logging.info('No existing DICOM ImageSet_%s. Generating ...' % imgsetid)
        # Initialize for CT DICOM creation.
        self._initializeForDicom('CT', imgsetid)
        self._createCTfromData(imgsetid)
        logging.info('DICOM ImageSet generated.')

    def _createCTfromData(self, imgsetid) -> bool:
        datafile = '%s/ImageSet_%s.img' % (self.PFPath, imgsetid)
        if not os.path.isfile(datafile):
            print('No CT data file found: %s' % datafile)
            logging.error('No CT data file found: %s' % datafile)
            return False
        
        for i in range(self.ImgSetInfo.NumberOfImages):
            file_meta = FileMetaDataset()
            file_meta.TransferSyntaxUID = self.TransferSyntaxUID
            file_meta.MediaStorageSOPClassUID    = self.StorageSOPClassUID
            file_meta.MediaStorageSOPInstanceUID = self.StorageSOPInstanceUID[i] #self.ImageInfo[i].InstanceUID

            ofname = '%s/CT_%s.%s.dcm' % (self.OutPath, str(i).zfill(3), self.SOPInstanceUID[i])
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
            self._setInstanceUID(ds, self.CTSOPInstanceUID[i])

            pydicom.dataset.validate_file_meta(ds.file_meta, enforce_standard=True)
            ds.save_as(ofname, write_like_original=False)
            logging.info('CT DICOM file saved: %s' % ofname)

        return True

    # OK
    def _getContourImageSequence(self):
        seq = pydicom.sequence.Sequence()
        for i in range(self.ImgSetInfo.NumberOfImages):
            ds_img = Dataset()
            ds_img.ReferencedSOPClassUID = self.CTSOPClassUID
            ds_img.ReferencedSOPInstanceUID = self.CTSOPInstanceUID[i]
            seq.append(ds_img)
        return seq

    # OK
    def _getRTReferencedSeriesSequence(self):
        seq = pydicom.sequence.Sequence()
        ds_series = Dataset()
        ds_series.SeriesInstanceUID = self.SeriesSOPInstanceUID
        ds_series.ContourImageSequence = self._getContourImageSequence()
        seq.append(ds_series)
        return seq

    # OK
    def _getRTReferencedStudySquence(self):
        seq = pydicom.sequence.Sequence()
        ds_refstudy = Dataset()
        ds_refstudy.ReferencedSOPClassUID = self.StudySOPClassUID
        ds_refstudy.ReferencedSOPInstanceUID = self.StudySOPInstanceUID
        ds_refstudy.RTReferencedSeriesSequence = self._getRTReferencedSeriesSequence()
        seq.append(ds_refstudy)
        return seq

    # OK
    def _getReferencedFrameOfReferenceSequence(self):
        seq = pydicom.sequence.Sequence()
        ds_refframe = Dataset()
        ds_refframe.FrameOfReferenceUID = self.FrameOfReferenceUID
        ds_refframe.RTReferencedStudySequence = self._getRTReferencedStudySquence()
        seq.append(ds_refframe)
        return seq

    # Not find in Eclipse RS export. Confirm later.
    # def _getPredecessorStructureSetSequence(self, ds):
    #     seq = pydicom.sequence.Sequence()
    #     ds_predstruct = Datase()
    #     ds_predstruct.ReferencedSOPClassUID = self.ClassUID
    #     ds_predstruct.ReferencedSOPInstanceUID = 
    #     return seq

    # OK
    def _getStructureSetROISequence(self):
        seq = pydicom.sequence.Sequence()

        # read from plan.points
        roi_number = 0
        for poi in self.PlanPoints.Poi:
            roi_number += 1
            ds_roi = Dataset()
            ds_roi.ROINumber = roi_number
            ds_roi.ROIGenerationAlgorithm = 'SEMIAUTOMATIC'
            ds_roi.ROIName = poi.Name
            ds_roi.ReferencedFrameOfReferenceUID = self.FrameOfReferenceUID
            seq.append(ds_roi)

        # read from plan.roi with roi_number continue
        for roi in self.PlanROI.roi:
            roi_number += 1
            ds_roi = Dataset()
            ds_roi.ROINumber = roi_number
            ds_roi.ROIName = roi.name
            ds_roi.ROIGenerationAlgorithm = 'SEMIAUTOMATIC'
            ds_roi.ReferencedFrameOfReferenceUID = self.FrameOfReferenceUID
            seq.append(ds_roi)

        return seq

    # OK
    def _setStructureSetModule(self, ds):
        ds.InstanceNumber = 0
        ds.StructureSetLabel = self.PlanInfo.PlanName
        ds.StructureSetName  = 'POIandROI'
        ds.StructureSetDate = ''
        ds.StructureSetTime = ''
        ds.ReferencedFrameOfReferenceSequence = self._getReferencedFrameOfReferenceSequence()
        # ds.PredecessorStructureSetSequence = self._getPredecessorStructureSetSequence(ds)
        ds.StructureSetROISequence = self._getStructureSetROISequence()

    def _getClosestImageInstanceUID(self, z): # in cm
        # ds.SliceLocation = 10.0*self.ImageInfo[index].CouchPos
        uid = self.CTSOPInstanceUID[0]
        for img_info in self.ImageInfo:
            if abs(z - img_info.TablePosition) < 0.02:  # in cm
                uid = self.CTSOPInstanceUID[img_info.SliceNumber-1]
                return uid
        return uid

    # OK
    def _getContourSequence(self, roi, ctype='POINT'):
        seq = pydicom.sequence.Sequence()
        if ctype == 'POINT':
            ds_point = Dataset()
            ds_point.ContourGeometricType = ctype
            ds_point.NumberOfContourPoints = 1
            ds_point.ContourData = self.transCoord([
                roi.XCoord, roi.YCoord, roi.ZCoord
            ])
            # print(roi.XCoord, roi.YCoord, roi.ZCoord)
            # print(ds_point.ContourData)
            ds_point.ContourImageSequence = pydicom.sequence.Sequence()
            ds_contourimage = Dataset()
            ds_contourimage.ReferencedSOPClassUID = self.CTSOPClassUID
            ds_contourimage.ReferencedSOPInstanceUID = self._getClosestImageInstanceUID(roi.ZCoord)
            ds_point.ContourImageSequence.append(ds_contourimage)
            seq.append(ds_point)
        if ctype == 'CLOSED_PLANAR':
            roi = self.PlanROI.roi[0]
            for curve in roi.curve:
                ds_planar = Dataset()
                ds_planar.ContourGeometricType = ctype
                ds_planar.NumberOfContourPoints = curve.num_points
                ds_planar.ContourData = self.transCoord(curve.points)
                ds_planar.ContourImageSequence = pydicom.sequence.Sequence()
                ds_contourimage = Dataset()
                ds_contourimage.ReferencedSOPClassUID = self.CTSOPClassUID
                ds_contourimage.ReferencedSOPInstanceUID = self._getClosestImageInstanceUID(curve.points[2])
                ds_planar.ContourImageSequence.append(ds_contourimage)
                seq.append(ds_planar)
                
        return seq

    # OK
    def _getROIContourSequence(self):
        from pftools.PFColor import PFColor
        seq = pydicom.sequence.Sequence()
        # POI
        roi_number = 0
        for poi in self.PlanPoints.Poi:            
            roi_number += 1
            ds_roicontour = Dataset()
            ds_roicontour.ROIDisplayColor = PFColor(poi.Color).getRGB()
            ds_roicontour.ReferencedROINumber = roi_number
            ds_roicontour.ContourSequence = self._getContourSequence(poi, ctype='POINT')
            seq.append(ds_roicontour)

        # plan.roi, continue with roi_number
        for roi in self.PlanROI.roi:
            roi_number += 1
            ds_roicontour = Dataset()
            ds_roicontour.ROIDisplayColor = PFColor(roi.color).getRGB()
            ds_roicontour.ReferencedROINumber = roi_number
            ds_roicontour.ContourSequence = self._getContourSequence(roi, ctype='CLOSED_PLANAR')
            seq.append(ds_roicontour)
        return seq

    # OK
    def _setROIContourModule(self, ds):
        ds.ROIContourSequence = self._getROIContourSequence()


    def _getRTROIObservationsSequence(self, ds):
        seq = pydicom.sequence.Sequence()

        # read from plan.points
        roi_number = 0
        for poi in self.PlanPoints.Poi:
            roi_number += 1
            ds_roi = Dataset()
            ds_roi.ObservationNumber = roi_number
            ds_roi.ReferencedROINumber = roi_number
            ds_roi.ROIObservationLabel = poi.Name
            ds_roi.RTROIInterpretedType = 'MARKER'
            ds_roi.ROIInterpreter = ''
            seq.append(ds_roi)

        # read from plan.roi with roi_number continue
        for roi in self.PlanROI.roi:
            roi_number += 1
            ds_roi = Dataset()
            ds_roi.ObservationNumber = roi_number
            ds_roi.ReferencedROINumber = roi_number
            ds_roi.ROIObservationLabel = roi.name
            ds_roi.RTROIInterpretedType = 'ORGAN'
            ds_roi.ROIInterpreter = ''
            seq.append(ds_roi)

        return seq

    # OK now
    def _setRTROIObservationsModule(self, ds):
        ds.RTROIObservationsSequence = self._getRTROIObservationsSequence(ds)


    def createDicomRS(self, planid=0):
        self._initializeForDicom('RS', planid)

        file_meta = FileMetaDataset()
        file_meta.TransferSyntaxUID = self.TransferSyntaxUID
        file_meta.MediaStorageSOPClassUID    = self.StorageSOPClassUID
        file_meta.MediaStorageSOPInstanceUID = self.StorageSOPInstanceUID

        ofname = '%s/RS.%s.dcm' % (self.OutPath, self.RSSOPInstanceUID)
        ds = FileDataset(ofname, {}, file_meta=file_meta, preamble=self.Preamble)

        self._setSOPCommon(ds)
        self._setPatientModule(ds)
        self._setFrameOfReference(ds)
        self._setStudyModule(ds)
        self._setSeriesModule(ds)
        self._setEquipmentModule(ds)
        self._setStructureSetModule(ds)
        self._setROIContourModule(ds)
        self._setRTROIObservationsModule(ds)
        self._setInstanceUID(ds, self.RSSOPInstanceUID)

        pydicom.dataset.validate_file_meta(ds.file_meta, enforce_standard=True)
        ds.save_as(ofname, write_like_original=False)
        logging.info('RS DICOM file saved: %s' % ofname)



if __name__ == '__main__':
    prjpath = os.path.dirname(os.path.abspath(__file__))+'/../'

    FORMAT = "[%(asctime)s %(levelname)s - %(funcName)s] %(message)s"
    logging.basicConfig(format=FORMAT, filename=prjpath+'logs/test.log', level=logging.INFO)

    print('Start creating DICOM Files ...')
    pfDicom = PFDicom(prjpath+'examples/Patient_6204')
    
    for imgset in pfDicom.Patient.ImageSetList.ImageSet:
        pfDicom.createDicomCT(imgset.ImageSetID)
        print('DICOM ImageSet_%s created!' % imgset.ImageSetID) 
    
    for plan in pfDicom.Patient.PlanList.Plan:
        pfDicom.createDicomRS(plan.PlanID)
        print('DICOM RTStruct_%s created!' % plan.PlanID)
