from logging import lastResort
import os
import pytest
from pftools import readPFile
import logging

prjpath = os.path.dirname(os.path.abspath(__file__))+'/../'
FORMAT = "[%(asctime)s %(levelname)s - %(funcName)s] %(message)s"
logging.basicConfig(format=FORMAT, filename=prjpath+'logs/pytest.log', level=logging.WARNING)

Patient     = readPFile(prjpath+'examples/Patient_6204/Patient', 'Patient')
Header      = readPFile(prjpath+'examples/Patient_6204/ImageSet_0.header', 'ImageSet.header')
ImgSetInfo  = readPFile(prjpath+'examples/Patient_6204/ImageSet_0.ImageInfo', 'ImageSet.ImageInfo')
ImageSet    = readPFile(prjpath+'examples/Patient_6204/ImageSet_0.ImageSet', 'ImageSet.ImageSet')
PlanLaser   = readPFile(prjpath+'examples/Patient_6204/Plan_0/plan.Laser', 'plan.Laser')
PatientSetup= readPFile(prjpath+'examples/Patient_6204/Plan_0/plan.PatientSetup', 'plan.PatientSetup')
PlanInfo    = readPFile(prjpath+'examples/Patient_6204/Plan_0/plan.PlanInfo', 'plan.PlanInfo')
PlanPoints  = readPFile(prjpath+'examples/Patient_6204/Plan_0/plan.Points', 'plan.Points')
ROIList     = readPFile(prjpath+'examples/Patient_6204/Plan_0/plan.roi', 'plan.roi')
PlanTrial0  = readPFile(prjpath+'examples/Patient_6204/Plan_0/plan.Trial', 'plan.Trial')
PlanTrial1  = readPFile(prjpath+'examples/Patient_6204/Plan_1/plan.Trial', 'plan.Trial')
     
def test_patient_read():
    assert (Patient.PlanList.Plan[0].PlanName,
            Patient.LastName,
            Patient.MedicalRecordNumber,
            Patient.ImageSetList.ImageSet[0].ImageName,
            Patient.PlanList.Plan[1].PlanID,
            Patient.PlanList.Plan[1].PrimaryCTImageSetID
        ) == (
            'LT BREAST',
            'LAST',
            '00003030',
            'ImageSet_0',
            1,
            0
        )

def test_imageset_header_read():
    assert (Header.y_dim,
            Header.z_pixdim,
            Header.x_start,
            Header.patient_position,
            Header.study_id,
            Header.exam_id,
            Header.z_dim
        ) == (
            512,
            0.3,
            -25.949219,
            'HFS',
            5585,
            12636,
            98
        )

def test_imageinfo_read():
    assert (ImgSetInfo.ImageInfo[1].TablePosition,
            ImgSetInfo.ImageInfo[2].SeriesUID,
            ImgSetInfo.ImageInfo[3].InstanceUID,
        ) == (
            -31.4688,
            '2.16.840.1.113662.2.12.0.3137.1168342749.1092',
            '2.16.840.1.113662.2.12.0.3137.1168342749.1108'
        )

def test_imageset_read():
    assert (ImageSet.ImageSetID,
            ImageSet.ExamID,
            ImageSet.NumberOfImages,
            ImageSet.ScanTimeFromScanner
        ) == (
            0,
            '12636',
            98,
            '2007-01-09'
        )

def test_plan_laser_read():
    assert (PlanLaser.LaserCenter.Name,
            PlanLaser.LaserCenter.ZCoord,
            PlanLaser.LaserCenter.CoordSys
        ) == (
            'Laser Center',
            -15.5688,
            'CT'
        )

def test_patientsetup_read():
    assert (PatientSetup.Position,
            PatientSetup.Orientation,
            PatientSetup.TableMotion
        ) == (
            'On back (supine)',
            'Head First Into Scanner',
            'Table Moves Into Scanner'
        )

def test_planinfo_read():
    assert (PlanInfo.PlanName,
            PlanInfo.FirstName,
            PlanInfo.MedicalRecordNumber,
            PlanInfo.PrimaryImageType
        ) == (
            'LT BREAST',
            'FRSTNAM',
            '00003030',
            'Images'
        )
    
def test_planpoints_read():
    assert (PlanPoints.Poi[0].Name,
            PlanPoints.Poi[1].ZCoord,
            PlanPoints.Poi[2].CoordSys,
            PlanPoints.Poi[1].CoordinateFormat
        ) == (
            'CT REF',
            -15.5688,
            'CT',
            '%6.2f'
        )

def test_planroi_read():
    assert (ROIList.roi[0].name,
            ROIList.roi[0].num_curve,
            ROIList.roi[1].curve[0].num_points,
            ROIList.roi[1].curve[1].points[10],
            ROIList.roi[0].density,
            ROIList.roi[1].density_units
        ) == (
            'scar',
            11,
            39,
            -70.7119,
            1,
            'g/cm^3'
        )

def test_plantrial1_read():
    assert (PlanTrial1.Trial.Name,
            PlanTrial1.Trial.DoseGridVoxelSizeX,
            PlanTrial1.Trial.DoseGridOriginY,
            PlanTrial1.Trial.PrescriptionList.Prescription[0].PrescriptionDose,
            PlanTrial1.Trial.BeamList.Beam[0].IsocenterName,
            PlanTrial1.Trial.BeamList.Beam[0].DosePerMuAtPrescriptionPoint,
            PlanTrial1.Trial.BeamList.Beam[0].MachineNameAndVersion,
            PlanTrial1.Trial.BeamList.Beam[0].SetBeamType
        ) == (
            'Direct Electron',
            0.4,
            -78.0062,
            1250,
            'e iso',
            1,
            'EX_7p4: 2006-03-06 11:59:38',
            'Static'
        )