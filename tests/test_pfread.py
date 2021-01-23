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

def test0_plantrial0_read():
    assert (PlanTrial0.Trial.Name,
            PlanTrial0.Trial.DoseGridVoxelSizeX,
            PlanTrial0.Trial.DoseGridOriginY,
            PlanTrial0.Trial.PrescriptionList.Prescription[0].PrescriptionDose,
            PlanTrial0.Trial.BeamList.Beam[0].IsocenterName,
            PlanTrial0.Trial.BeamList.Beam[0].DosePerMuAtPrescriptionPoint,
            PlanTrial0.Trial.BeamList.Beam[0].MachineNameAndVersion,
            PlanTrial0.Trial.BeamList.Beam[0].Modality,
            PlanTrial0.Trial.BeamList.Beam[0].MachineEnergyName,
            PlanTrial0.Trial.BeamList.Beam[0].SetBeamType
        ) == (
            'sMLC',
            0.4,
            -83.7535,
            4250,
            'isocentre',
            1,
            'EX_7p4: 2006-03-06 11:59:38',
            'Photons',
            '6X',
            'Step & Shoot MLC'
        )

def test0_plantrial1_read():
    assert (PlanTrial1.Trial.Name,
            PlanTrial1.Trial.DoseGridVoxelSizeX,
            PlanTrial1.Trial.DoseGridOriginY,
            PlanTrial1.Trial.PrescriptionList.Prescription[0].PrescriptionDose,
            PlanTrial1.Trial.BeamList.Beam[0].IsocenterName,
            PlanTrial1.Trial.BeamList.Beam[0].DosePerMuAtPrescriptionPoint,
            PlanTrial1.Trial.BeamList.Beam[0].MachineNameAndVersion,
            PlanTrial1.Trial.BeamList.Beam[0].Modality,
            PlanTrial1.Trial.BeamList.Beam[0].MachineEnergyName,
            PlanTrial1.Trial.BeamList.Beam[0].SetBeamType
        ) == (
            'Direct Electron',
            0.4,
            -78.0062,
            1250,
            'e iso',
            1,
            'EX_7p4: 2006-03-06 11:59:38',
            'Electrons',
            '16e',
            'Static'
        )

def test1_plantrial0_controlpoint_read():
    cp1 = PlanTrial0.Trial.BeamList.Beam[0].CPManager.CPManagerObject[0].ControlPointList.ControlPoint[1]
    assert (cp1.Gantry,
            cp1.LeftJawPosition,
            cp1.WedgeContext.WedgeName,
            cp1.WedgeContext.Orientation,
            cp1.WedgeContext.Angle,
            cp1.ModifierList.BeamModifier[0].Name,
            cp1.ModifierList.BeamModifier[0].StructureToBlock,
            cp1.ModifierList.BeamModifier[0].Margin,
            cp1.ModifierList.BeamModifier[0].InsideMode,
            cp1.ModifierList.BeamModifier[0].ContourList.CurvePainter[1].Curve.RawData.Points[1],
            cp1.MLCLeafPositions.RawData.NumberOfPoints,
            cp1.MLCLeafPositions.RawData.Points[30],
            cp1.MLCLeafPositions.RawData.Points[95],
            cp1.MLCLeafPositions.RowLabelList.RowLabel[1].String
        ) == (
            306,
            4.2,
            'No Wedge',
            'NoWedge',
            'No Wedge',
            'BeamModifier_1',
            'Manual',
            0,
            'Block',
            -9.29816,
            60,
            3.9,
            6.3,
            '  2. Y : -18.50 cm'
        )

def test1_plantrial1_controlpoint_read():
    cp0 = PlanTrial1.Trial.BeamList.Beam[0].CPManager.CPManagerObject[0].ControlPointList.ControlPoint[0]
    assert (cp0.Gantry,
            cp0.LeftJawPosition,
            cp0.WedgeContext.WedgeName,
            cp0.WedgeContext.Orientation,
            cp0.WedgeContext.Angle,
            cp0.ModifierList.BeamModifier[0].Name,
            cp0.ModifierList.BeamModifier[0].StructureToBlock,
            cp0.ModifierList.BeamModifier[0].Margin,
            cp0.ModifierList.BeamModifier[0].InsideMode,
            cp0.MLCLeafPositions.RawData.NumberOfPoints,
            cp0.MLCLeafPositions.RawData.Points[1],
            cp0.MLCLeafPositions.RawData.Points[119],
            cp0.MLCLeafPositions.RowLabelList.RowLabel[1].String
        ) == (
            90,
            3,
            'No Wedge',
            'NoWedge',
            'No Wedge',
            'BeamModifier_1',
            'boost',
            1,
            'Expose',
            60,
            3,
            3,
            '  2. Y : -18.50 cm'
        )

def test2_plantrial0_controlpoint_read():
    beam1 = PlanTrial0.Trial.BeamList.Beam[1]
    assert (beam1.UseMLC,
            beam1.ElectronApplicatorName,
            beam1.Bolus.Type,
            beam1.Bolus.Density,
            beam1.Bolus.Thickness,
            beam1.Compensator.IsValid,
            beam1.CompensatorScaleFactor,
            beam1.MonitorUnitInfo.PrescriptionDose,
            beam1.MonitorUnitInfo.PrescriptionPointDepth,
            beam1.Name,
            beam1.SSD
        ) == (
            1,
            'None',
            'No bolus',
            1,
            2,
            0,
            0,
            39.8434,
            8.19073,
            'Med 15',
            91.8093
        )
def test2_plantrial1_controlpoint_read():
    beam0 = PlanTrial1.Trial.BeamList.Beam[0]
    assert (beam0.UseMLC,
            beam0.ElectronApplicatorName,
            beam0.Bolus.Type,
            beam0.Bolus.Density,
            beam0.Bolus.Thickness,
            beam0.Compensator.IsValid,
            beam0.CompensatorScaleFactor,
            beam0.MonitorUnitInfo.PrescriptionDose,
            beam0.MonitorUnitInfo.PrescriptionPointDepth,
            beam0.SSD
        ) == (
            0,
            '6x6 cone',
            'No bolus',
            1,
            2,
            0,
            0,
            263.158,
            3.31767,
            100
        )