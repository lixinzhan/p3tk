import os
import struct
import sys
import logging
import datetime
from typing import List, Sequence

from numpy.core.fromnumeric import shape

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
        if dst not in ['CT', 'RS', 'RP', 'RD']:
            logging.error('Incorrect DICOM format: %s' % dst)
            print('Error: Incorrect DICOM format: %s' % dst)

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

        if dst == 'RS' or dst == 'RD' or dst == 'RP':
            self.PlanID = id
            self.ImageSetID = self.PlanImageSetMap[id]
            self.ImgSetHeader = readImageSetHeader(self.PFPath, self.ImageSetID)
            self.ImgSetInfo = readImageSetInfo(self.PFPath, self.ImageSetID)
            self.ImageInfo = readImageInfo(self.PFPath, self.ImageSetID).ImageInfo
            self.PlanPatientSetup = readPlanPatientSetup(self.PFPath, self.PlanID)
            self.PlanInfo = readPlanInfo(self.PFPath, self.PlanID)
            self.PlanPoints = readPlanPoints(self.PFPath, self.PlanID)
            self.PlanROI = readPlanROI(self.PFPath, self.PlanID)

        if dst == 'RD' or dst == 'RP':
            self.PlanTrial = readPlanTrial(self.PFPath, self.PlanID)

        self.TransferSyntaxUID = pydicom.uid.ExplicitVRLittleEndian

        # Entropy src based SOPInstanceUID for CT, RS, RP, and RD
        self.CTSOPInstanceUID = [] #pydicom.uid.generate_uid() # one for each image
        for i in range(self.ImgSetInfo.NumberOfImages):
            entropy_src = [ self.Patient.MedicalRecordNumber, str(self.ImageSetID), 
                            str(self.ImageInfo[i].SliceNumber), 'CT']
            self.CTSOPInstanceUID.append(   # last 3 characters are the slice number
                pydicom.uid.generate_uid(entropy_srcs=entropy_src)[:-3] + str(i+1).zfill(3)
                )
        # Padding characters 7 for RS, 8 for RD, 9 for RP, plus planid, at the UID end.
        entropy_src = [ self.Patient.MedicalRecordNumber, str(self.ImageSetID), str(self.PlanID), 'RS']
        self.RSSOPInstanceUID = pydicom.uid.generate_uid(entropy_srcs=entropy_src)[:-3] + str(self.PlanID).rjust(3,'7')
        entropy_src = [ self.Patient.MedicalRecordNumber, str(self.ImageSetID), str(self.PlanID), 'RP']
        self.RPSOPInstanceUID = pydicom.uid.generate_uid(entropy_srcs=entropy_src)[:-3] + str(self.PlanID).rjust(3,'9')
        entropy_src = [ self.Patient.MedicalRecordNumber, str(self.ImageSetID), str(self.PlanID), 'RD']
        self.RDSOPInstanceUID = pydicom.uid.generate_uid(entropy_srcs=entropy_src)[:-3] + str(self.PlanID).rjust(3,'8')

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

        # replace last 3 chars for easy identifying UIDs: 4-Frame, 5-Study, 6-Series
        entropy_src = [ self.Patient.MedicalRecordNumber, str(self.ImageSetID), 'Frame']
        self.FrameOfReferenceUID = pydicom.uid.generate_uid(entropy_srcs=entropy_src)[:-3] + '444'

        self.StudySOPClassUID = self.SOPClassUID
        #entropy_src = [ self.Patient.MedicalRecordNumber, str(self.ImageSetID), 'Study']
        self.StudySOPInstanceUID = pydicom.uid.generate_uid()[:-3] + '555'

        # self.SeriesSOPClassUID = ssopuids.CTImageStorage
        #entropy_src = [ self.Patient.MedicalRecordNumber, str(self.ImageSetID), 'Series']
        self.SeriesSOPInstanceUID = pydicom.uid.generate_uid()[:-3] + '666'


        # yyyy-mm-dd to yyyymmdd   
        img_set = self.Patient.ImageSetList.ImageSet[self.ImageSetID]
        self.ScanDate = self.ImgSetHeader.date.split()[0].replace('-','')

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

    def _setFrameOfReference(self, ds):  # not to be included in RS
        ds.FrameOfReferenceUID = self.FrameOfReferenceUID
        ds.PositionReferenceIndicator = '' #'RF'  # not used, annotation purpose only

    def _setInstanceUID(self, ds, inst_uid=''):
        ds.SOPInstanceUID = inst_uid
        if self.DICOMFORMAT == 'CT':
            ds.InstanceCreationDate = self.ScanDate
        elif self.DICOMFORMAT in ['RS', 'RD', 'RP']:
            ds.InstanceCreationDate = self.PlanPatientSetup.ObjectVersion.WriteTimeStamp[:10].replace('-','')
            ds.InstanceCreationTime = self.PlanPatientSetup.ObjectVersion.WriteTimeStamp[11:].replace(':','')

    # def _getReferencedStudySequence(self):
    #     seq = pydicom.sequence.Sequence()
    #     ref_study = Dataset()
    #     ref_study.ReferencedSOPClassUID = self.CTSOPClassUID
    #     ref_study.ReferencedSOPInstanceUID = self.StudySOPInstanceUID
    #     seq.append(ref_study)

    def _setStudyModule(self, ds):
        ds.StudyDate = self.ScanDate
        ds.StudyTime = '000000'
        ds.StudyInstanceUID = self.StudySOPInstanceUID
        if not(self.ImgSetHeader.study_id is None or self.ImgSetHeader.study_id.strip() == ''):
            ds.StudyID = self.ImgSetHeader.study_id
        elif not(self.ImgSetHeader.exam_id is None or self.ImgSetHeader.exam_id.strip() == ''):
            ds.StudyID = self.ImgSetHeader.exam_id
        else:
            ds.StudyID = self.Patient.MedicalRecordNumber[-4:]
        ds.AccessionNumber = ''
        ds.ReferringPhysicianName = ''
        # if self.DICOMFORMAT != 'CT':
        #     ds.ReferencedStudySequence = self._getReferencedStudySequence()

    def _setSeriesModule(self, ds):
        # Series Number (0020,0011) is a human readable numeric label, which may be empty 
        # and is not unique within any defined scope; it is required to have the same value 
        # for all instances that have the same Series Instance UID (0020,000E) 
        # (this is true of all attributes for the same "entity"), but there is no requirement 
        # that it be different for different series (though this is often the case for 
        # different series in the same study, especially if produced by the same equipment) 
        ds.SeriesInstanceUID = self.SeriesSOPInstanceUID
        ds.SeriesNumber = self.ImgSetHeader.exam_id
        if self.DICOMFORMAT == 'CT':
            ds.Modality = 'CT'
            ds.PatientPosition = self.ImgSetHeader.patient_position
        elif self.DICOMFORMAT == 'RS':
            ds.Modality = 'RTSTRUCT'
        elif self.DICOMFORMAT == 'RP':
            ds.Modality = 'RTPLAN'
        elif self.DICOMFORMAT == 'RD':
            ds.Modality = 'RTDOSE'
        else:
            ds.Modality = self.DICOMFORMAT
        # ds.SeriesDate = self.ScanDate   # Optional
        # ds.SeriesTime = ''              # Optional
            

    def _setEquipmentModule(self, ds):
        if self.DICOMFORMAT == 'CT':
            ds.Manufacturer = self.ImgSetHeader.manufacturer
            ds.ManufacturerModelName = self.ImgSetHeader.model
        else:
            ds.Manufacturer = 'P3TK'
            # ds.ManufactureModelName = self.DICOMFORMAT
        # ds.InstitutionName = dcmcommon.InstitutionName        # Optional
        # ds.InstitutionAddress = dcmcommon.InstitutionAddress  # Optional
        ds.StationName = dcmcommon.StationName

    def _setGeneralCTImageModule(self, ds):
        # General Image Module
        ds.ImageType = r"ORIGINAL\PRIMARY\AXIAL"
        ds.AcquisitionDate = self.ScanDate
        ds.ContentDate = self.ScanDate
        ds.AcquisitionNumber = ''
        ds.InstanceNumber = ''   # probably this can be ignored?
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
        # ds.SliceLocation = 10.0*self.ImageInfo[index].CouchPos
        ds.SliceLocation = -10.0*self.ImageInfo[index].TablePosition
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

            ofname = '%s/CT_%s.%s.dcm' % (self.OutPath, str(i+1).zfill(3), self.SOPInstanceUID[i])
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
        # ds.InstanceNumber = 0   # not to be included.
        ds.StructureSetLabel = self.PlanInfo.PlanName
        ds.StructureSetName  = 'POIandROI'
        ds.StructureSetDate = ''
        ds.StructureSetTime = ''
        ds.ApprovalStatus = 'UNAPPROVED'
        ds.ReferencedFrameOfReferenceSequence = self._getReferencedFrameOfReferenceSequence()
        # ds.PredecessorStructureSetSequence = self._getPredecessorStructureSetSequence(ds)
        ds.StructureSetROISequence = self._getStructureSetROISequence()

    def _getClosestImageInstanceUID(self, z): # in cm
        uid = 'unknown'
        for img_info in self.ImageInfo:
            if abs(z - img_info.TablePosition) < 0.02:  # in cm
                uid = self.CTSOPInstanceUID[img_info.SliceNumber-1]
                # print('Slice #: %s,  TablePosition: %s, InstanceUID: %s' % (img_info.SliceNumber, img_info.TablePosition, uid))
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
            for curve in roi.curve:
                ds_planar = Dataset()
                ds_planar.ContourGeometricType = ctype
                ds_planar.NumberOfContourPoints = curve.num_points
                ds_planar.ContourData = self.transCoord(curve.points)
                ds_planar.ContourImageSequence = pydicom.sequence.Sequence()
                ds_contourimage = Dataset()
                ds_contourimage.ReferencedSOPClassUID = self.CTSOPClassUID
                ds_contourimage.ReferencedSOPInstanceUID = self._getClosestImageInstanceUID(curve.points[2])
                # print('--> ZCoord: %s' % curve.points[2])
                # print('--> ROI: %s  ContourPoints: %s   DataLength: %s' % (roi.name, ds_planar.NumberOfContourPoints, len(ds_planar.ContourData)))
                # for i in range(curve.num_points):
                #     print('%s: %s, %s, %s' % (i, ds_planar.ContourData[i*3], ds_planar.ContourData[i*3+1], ds_planar.ContourData[i*3+2]))
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

        ofname = '%s/RS_%s.%s.dcm' % (self.OutPath, str(planid).zfill(3), self.RSSOPInstanceUID)
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

    def _getBeamDose(self, beam) -> np.array:
        import struct

        prescription = self.PlanTrial.Trial.PrescriptionList.Prescription[0]
        for presc in self.PlanTrial.Trial.PrescriptionList.Prescription:
            if presc.Name == beam.PrescriptionName:
                prescription = presc

        binary_number = beam.DoseVolume.split(':')[1][:-1]
        beam_mu = beam.MonitorUnitInfo.PrescriptionDose
        data_block = []
        binary_file = '%s/Plan_%s/plan.Trial.binary.%s' % (self.PFPath, self.PlanID, str(binary_number).zfill(3))
        # print('%s has binary number %s --> %s, result in binary file %s' % (beam.Name, 
        #         beam.DoseVolume, binary_number, binary_file))
        with open(binary_file, 'rb') as bfile:
            data_element = bfile.read(4)
            while data_element:
                v_raw = struct.unpack(">f", data_element)[0]
                # from fraction dose to total. What is actually stored in binary files: MU or fraction dose?
                v_cnv = v_raw * prescription.NumberOfFractions * beam_mu / 100
                data_block.append(v_cnv)
                data_element = bfile.read(4)

        # # re-organize data
        # nx = self.PlanTrial.Trial.DoseGridDimensionX
        # ny = self.PlanTrial.Trial.DoseGridDimensionY
        # nz = self.PlanTrial.Trial.DoseGridDimensionZ
        # data_array = np.array(data_block, dtype=float).reshape(nz,ny,nx)
        # shuffled_data = data_array[::, ::, ::]

        return np.array(data_block, dtype=float)

    def _setDoseImageModule(self, ds):
        x_orig = self.PlanTrial.Trial.DoseGridOriginX
        y_orig = self.PlanTrial.Trial.DoseGridOriginY
        z_orig = self.PlanTrial.Trial.DoseGridOriginZ
        dx = self.PlanTrial.Trial.DoseGridVoxelSizeX
        dy = self.PlanTrial.Trial.DoseGridVoxelSizeY
        dz = self.PlanTrial.Trial.DoseGridVoxelSizeZ
        nx = self.PlanTrial.Trial.DoseGridDimensionX
        ny = self.PlanTrial.Trial.DoseGridDimensionY
        nz = self.PlanTrial.Trial.DoseGridDimensionZ
        # Shift applied to y. Probably ref orig is at different side of the dose region for Y.
        [x0, y0, z0] = self.transCoord([x_orig, y_orig+dy*(ny-1), z_orig])
        print('orig: ', [x_orig,y_orig,z_orig], 'new: ', [x0,y0,z0])
        dx = dx * 10  # cm --> mm
        dy = dy * 10
        dz = dz * 10 
        ds.PixelSpacing = [dx, dy]
        ds.SliceThickness = None                    # dz ***************
        ds.Rows = ny
        ds.Columns = nx
        ds.NumberOfFrames = nz
        ds.GridFrameOffsetVector = [-dz*i for i in range(nz)]
        ds.FrameIncrementPointer = ds.data_element("GridFrameOffsetVector").tag
        ds.RescaleIntercept = 0
        ds.RescaleSlope = 1
        # ds.RescaleType = ''

        ds.ImagePositionPatient = [x0, y0, z0]
        if self.ImgSetHeader.patient_position in ['HFP', 'FFP']:
            ds.ImageOrientationPatient = [1.0,0.0,0.0,0.0,-1.0,-0.0]
        else: # if ds.PatientPosition in ['HFS', 'FFS']:
            ds.ImageOrientationPatient = [1.0,0.0,0.0,0.0,1.0,-0.0]
        # self.SliceLocation = ''

        totaldose = np.zeros(nx*ny*nz, dtype=float)
        for beam in self.PlanTrial.Trial.BeamList.Beam:
            beamdose = self._getBeamDose(beam)
            totaldose += beamdose
            # print('size: ', shape(beamdose), 'beamdose: ', beamdose[2000:2005])
            # print('size: ', shape(totaldose), 'totaldose: ', totaldose[2000:2005])

        ds.DoseGridScaling = 1.0e-6
        totaldose = totaldose/ds.DoseGridScaling
        scaleddose = totaldose.astype(np.int32)
        # print('scaleddose: ', scaleddose[2000:2005])
        smallestImagePixelValue = np.amin(scaleddose)
        largestImagePixelValue  = np.amax(scaleddose)
        print('Pixel value range: [%s, %s]' % (smallestImagePixelValue, largestImagePixelValue))
        length = nx*ny*nz
        format = ''
        if ds.BitsAllocated==32:
            format = 'I'*length
        elif ds.BitsAllocated==16:
            format = 'H'*length
        else:
            logging.error('BitsAllocated: %s is not supported!' % ds.BitsAllocated)
        ds.PixelData = struct.pack(format, *(scaleddose.tolist()))

    def _getReferencedRTPlanSequence(self, ds):
        seq = pydicom.sequence.Sequence()
        ds_refplan = Dataset()
        ds_refplan.ReferencedSOPClassUID = self.RPSOPClassUID
        ds_refplan.ReferencedSOPInstanceUID = self.RPSOPInstanceUID
        seq.append(ds_refplan)
        return seq

    def _setRTDoseModule(self, ds):
        ds.ContentDate = self.PlanTrial.Trial.ObjectVersion.WriteTimeStamp.split(' ')[0].replace('-','')
        ds.ContentTime = self.PlanTrial.Trial.ObjectVersion.WriteTimeStamp.split(' ')[1].replace(':','')
        ds.InstanceNumber = self.Patient.MedicalRecordNumber[-2:]+str(self.ImageSetID)+str(self.PlanID)
        ds.SamplesPerPixel = 1
        ds.PhotometricInterpretation = 'MONOCHROME2 '
        ds.BitsAllocated = 32
        ds.BitsStored = 32
        ds.HighBit = 31
        ds.PixelRepresentation = 0
        ds.DoseUnits = 'GY'
        ds.DoseType = 'PHYSICAL'
        # ds.SpatialTransformationOfDose = 'NONE'
        ds.DoseSummationType = 'PLAN'
        # self.DoseGridScaling = 1
        ds.ReferencedRTPlanSequence = self._getReferencedRTPlanSequence(ds)

    def createDicomRD(self, planid=0):
        self._initializeForDicom('RD', planid)

        file_meta = FileMetaDataset()
        file_meta.TransferSyntaxUID = self.TransferSyntaxUID
        file_meta.MediaStorageSOPClassUID    = self.StorageSOPClassUID
        file_meta.MediaStorageSOPInstanceUID = self.StorageSOPInstanceUID

        ofname = '%s/RD_%s.%s.dcm' % (self.OutPath, str(planid).zfill(3), self.RDSOPInstanceUID)
        ds = FileDataset(ofname, {}, file_meta=file_meta, preamble=self.Preamble)

        self._setSOPCommon(ds)
        self._setPatientModule(ds)
        self._setFrameOfReference(ds)
        self._setStudyModule(ds)
        self._setSeriesModule(ds)
        self._setEquipmentModule(ds)
        self._setRTDoseModule(ds)
        self._setDoseImageModule(ds)
        self._setInstanceUID(ds, self.RDSOPInstanceUID)

        pydicom.dataset.validate_file_meta(ds.file_meta, enforce_standard=True)
        ds.save_as(ofname, write_like_original=False)
        logging.info('RD DICOM file saved: %s' % ofname)

    def _getReferencedStructureSetSequence(self, ds):
        seq = pydicom.sequence.Sequence()
        ds_structset = Dataset()
        ds_structset.ReferencedSOPClassUID = self.RSSOPClassUID
        ds_structset.ReferencedSOPInstanceUID = self.RSSOPInstanceUID
        seq.append(ds_structset)
        return seq

    def _setRTGeneralPlanModule(self, ds):
        ds.InstanceNumber = '1'
        ds.RTPlanLabel = '%s %s' % ('Fake', self.PlanInfo.PlanName)
        ds.RTPlanName = self.PlanInfo.PlanName
        ds.RTPlanDate = '20210208'
        ds.RTPlanTime = '165246.72'
        # ds.TreatmentProtocols = ''
        ds.PlanIntent = 'CURATIVE'
        # ds.TreatmentSite = ''
        ds.RTPlanGeometry = 'PATIENT'
        ds.ReferencedStructureSetSequence = self._getReferencedStructureSetSequence(ds)
        ds.ApprovalStatus = 'UNAPPROVED'
    
    def _getDoseReferenceSequence(self):
        seq = pydicom.sequence.Sequence()
        ds_presc = Dataset()
        ds_presc.ReferencedROINumber = ''
        ds_presc.DoseReferenceUID = self.RDSOPInstanceUID
        ds_presc.DoseReferenceNumber = '1'
        ds_presc.DoseReferenceStructureType = 'SITE'
        # ds_presc.DoseReferencePointCoordinates = []
        ds_presc.DoseReferenceType = 'TARGET'
        # ds_presc.TargetPrescriptionDose = ''
        seq.append(ds_presc)
        return seq

    def _setRTPrescriptionModule(self, ds):
        ds.DoseReferenceSequence = self._getDoseReferenceSequence()

    def _setToleranceTablesModule(self, ds):
        pass

    def _getPatientSetupSequence(self):
        seq = pydicom.sequence.Sequence()
        ds_ptsetup = Dataset()
        ds_ptsetup.PatientPosition = 'HFS'
        ds_ptsetup.PatientSetupNumber = 1
        ds_ptsetup.SetupTechnique = 'ISOCENTRIC'
        seq.append(ds_ptsetup)
        return seq

    def _setRTPatientSetupModule(self, ds):
        ds.PatientSetupSequence = self._getPatientSetupSequence()

    def _getReferencedBeamSequence(self):
        seq = pydicom.sequence.Sequence()
        ds_beam = Dataset()
        # ds_beam.ReferencedDoseReferenceUID = ''
        ds_beam.BeamDose = '2'
        ds_beam.BeamMeterset = '200'
        # ds_beam.BeamDoseType = ''
        ds_beam.ReferencedBeamNumber = '1'
        seq.append(ds_beam)
        return seq

    def _getFractionGroupSequence(self):
        seq = pydicom.sequence.Sequence()
        ds_frac = Dataset()
        ds_frac.FractionGroupNumber = '1'
        ds_frac.NumberOfFractionsPlanned = '1'
        ds_frac.NumberOfBeams = '1'
        ds_frac.NumberOfBrachyApplicationSetups = '0'
        ds_frac.ReferencedBeamSequence = self._getReferencedBeamSequence()
        seq.append(ds_frac)
        return seq

    def _setRTFractionSchemeModule(self, ds):
        ds.FractionGroupSequence = self._getFractionGroupSequence()
        pass

    def _getBeamLimitingDevicePositionSequence(self):
        seq = pydicom.sequence.Sequence()
        ds_limdevx = Dataset()
        ds_limdevx.RTBeamLimitingDeviceType = 'ASYMX'
        ds_limdevx.LeafJawPositions = [-50, 50]
        seq.append(ds_limdevx)
        ds_limdevy = Dataset()
        ds_limdevy.RTBeamLimitingDeviceType = 'ASYMY'
        ds_limdevy.LeafJawPositions = [-50, 50]
        seq.append(ds_limdevy)
        return seq

    def _getReferencedDoseReferenceSequence(self, ref_coeff):
        seq = pydicom.sequence.Sequence()
        ds_doseref = Dataset()
        ds_doseref.CumulativeDoseReferenceCoefficient = ref_coeff
        ds_doseref.ReferencedDoseReferenceNumber = 1
        seq.append(ds_doseref)
        return seq

    def _getControlPointSequence(self): 
        seq = pydicom.sequence.Sequence()
        ds_cp1 = Dataset()
        ds_cp1.ControlPointIndex = 0
        ds_cp1.NominalBeamEnergy = 6
        ds_cp1.DoseRateSet = 600
        ds_cp1.BeamLimitingDevicePositionSequence = self._getBeamLimitingDevicePositionSequence()
        ds_cp1.GantryAngle = 0
        ds_cp1.GantryRotationDirection = 'NONE'
        ds_cp1.BeamLimitingDeviceAngle = 0
        ds_cp1.BeamLimitingDeviceRotationDirection = 'NONE'
        ds_cp1.PatientSupportAngle = 0
        ds_cp1.PatientSupportRotationDirection = 'NONE'
        ds_cp1.TableTopEccentricAngle = 0
        ds_cp1.TableTopEccentricRotationDirection = 'NONE'
        ds_cp1.TableTopVerticalPosition = ''
        ds_cp1.TableTopLongitudinalPosition = ''
        ds_cp1.TableTopLateralPosition = ''
        iso = []
        for poi in self.PlanPoints.Poi:
            if poi.Name == "isocentre":
                iso = self.transCoord([poi.XCoord, poi.YCoord, poi.ZCoord])
                break
            if poi.Name == "CT REF":
                iso = self.transCoord([poi.XCoord, poi.YCoord, poi.ZCoord])
        ds_cp1.IsocenterPosition = iso
        ds_cp1.CumulativeMetersetWeight = 0
        ds_cp1.TableTopPitchAngle = 0
        ds_cp1.TableTopPitchRotationDirection = 'NONE'
        ds_cp1.TableTopRollAngle = 0
        ds_cp1.TableTopRollRotationDirection = 'NONE'
        ds_cp1.ReferencedDoseReferenceSequence = self._getReferencedDoseReferenceSequence(0)
        seq.append(ds_cp1)

        ds_cp2 = Dataset()
        ds_cp2.ControlPointIndex = 1
        ds_cp2.CumulativeMetersetWeight = 1
        ds_cp2.ReferencedDoseReferenceSequence = self._getReferencedDoseReferenceSequence(1)
        seq.append(ds_cp2)
        return seq


    def _setRTBeamsModule(self, ds): # The most important module ?
        ds.BeamSequence = pydicom.sequence.Sequence()
        ds_bm = Dataset()
        ds_bm.Manufacturer = dcmcommon.TreatDeviceManufacturer
        ds_bm.ManufacturerModelName = dcmcommon.TreatDeviceModelName
        ds_bm.TreatmentMachineName = dcmcommon.TreatDeviceName       #'RT1TB'
        ds_bm.DeviceSerialNumber = dcmcommon.TreatDeviceSerialNumber #'2276'

        ds_bm.InstitutionName = dcmcommon.InstitutionName
        # ds_bm.InstitutionDepartmentName = ''
        ds_bm.PrimaryFluenceModeSequence = pydicom.sequence.Sequence()
        ds_fluencemode = Dataset()
        ds_fluencemode.FluenceMode = 'STANDARD'
        ds_bm.PrimaryFluenceModeSequence.append(ds_fluencemode)
        ds_bm.PrimaryDosimeterUnit = 'MU'
        ds_bm.SourceAxisDistance = 1000
        ds_bm.BeamLimitingDeviceSequence = pydicom.sequence.Sequence()
        ds_x = Dataset()
        ds_x.RTBeamLimitingDeviceType = 'ASYMX'
        ds_x.NumberOfLeafJawPairs = 1
        ds_bm.BeamLimitingDeviceSequence.append(ds_x)
        ds_y = Dataset()
        ds_y.RTBeamLimitingDeviceType = 'ASYMY'
        ds_y.NumberOfLeafJawPairs = 1
        ds_bm.BeamLimitingDeviceSequence.append(ds_y)
        ds_bm.BeamNumber = 1
        ds_bm.BeamName = 'Fake Beam'
        ds_bm.BeamType = 'STATIC'
        ds_bm.RadiationType = 'PHOTON'
        ds_bm.TreatmentDeliveryType = 'TREATMENT'
        ds_bm.NumberOfWedges = 0
        ds_bm.NumberOfCompensators = 0
        ds_bm.NumberOfBoli = 0
        ds_bm.NumberOfBlocks = 0
        ds_bm.FinalCumulativeMetersetWeight = 1
        ds_bm.NumberOfControlPoints = 2
        ds_bm.ControlPointSequence = self._getControlPointSequence()
        ds_bm.ReferencedPatientSetupNumber = 1
        ds_bm.ReferencedToleranceTableNumber = 0
        ds.BeamSequence.append(ds_bm)

    def createDicomRP(self, planid=0):
        self._initializeForDicom('RP', planid)

        file_meta = FileMetaDataset()
        file_meta.TransferSyntaxUID = self.TransferSyntaxUID
        file_meta.MediaStorageSOPClassUID    = self.StorageSOPClassUID
        file_meta.MediaStorageSOPInstanceUID = self.StorageSOPInstanceUID

        ofname = '%s/RP_%s.%s.dcm' % (self.OutPath, str(planid).zfill(3), self.RDSOPInstanceUID)
        ds = FileDataset(ofname, {}, file_meta=file_meta, preamble=self.Preamble)

        self._setSOPCommon(ds)
        self._setPatientModule(ds)
        self._setFrameOfReference(ds)
        self._setStudyModule(ds)
        self._setSeriesModule(ds)
        self._setEquipmentModule(ds)
        self._setInstanceUID(ds, self.RPSOPInstanceUID)

        self._setRTGeneralPlanModule(ds)
        self._setRTPrescriptionModule(ds)
        # self._setToleranceTablesModule(ds)
        self._setRTPatientSetupModule(ds)
        self._setRTFractionSchemeModule(ds)
        self._setRTBeamsModule(ds)

        pydicom.dataset.validate_file_meta(ds.file_meta, enforce_standard=True)
        ds.save_as(ofname, write_like_original=False)
        logging.info('RP DICOM file saved: %s' % ofname)

if __name__ == '__main__':
    prjpath = os.path.dirname(os.path.abspath(__file__))+'/../'

    FORMAT = "[%(asctime)s %(levelname)s - %(funcName)s] %(message)s"
    logging.basicConfig(format=FORMAT, filename=prjpath+'logs/test.log', level=logging.INFO)

    print('Start creating DICOM Files ...')
    pfDicom = PFDicom(prjpath+'examples/Patient_4604')
    #pfDicom = PFDicom('/home/lzhan/PinnBackup/Institution_48/Mount_0/Patient_4604/')
    
    for imgset in pfDicom.Patient.ImageSetList.ImageSet:
        pfDicom.createDicomCT(imgset.ImageSetID)
        print('DICOM ImageSet_%s created!' % imgset.ImageSetID) 
    
    for plan in pfDicom.Patient.PlanList.Plan:
        pfDicom.createDicomRS(plan.PlanID)
        print('DICOM RTStruct_%s created!' % plan.PlanID)

    for plan in pfDicom.Patient.PlanList.Plan:
        pfDicom.createDicomRD(plan.PlanID)
        print('DICOM RD for Plan_%s created!' % plan.PlanID)

    for plan in pfDicom.Patient.PlanList.Plan:
        pfDicom.createDicomRP(plan.PlanID)
        print('DICOM RP for Plan_%s created!' % plan.PlanID)
