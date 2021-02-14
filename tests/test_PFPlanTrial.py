import os
import pytest
import logging
from pftools.PFPlanTrial import PFPlanTrial
from pftools.readPFile import readPFile

prjpath = os.path.dirname(os.path.abspath(__file__))+'/../'
FORMAT = "[%(asctime)s %(levelname)s - %(funcName)s] %(message)s"
logging.basicConfig(format=FORMAT, filename=prjpath+'logs/pytest.log', level=logging.WARNING)

Pdict = readPFile(prjpath+'examples/Patient_6204/Plan_0/plan.Trial', 
                'plan.Trial', 'dict')
pfPlanTrial_0 = PFPlanTrial(**Pdict)

def test0_PFPlanTrial():
    cpmgr0 = pfPlanTrial_0.Trial[0].BeamList.Beam[0].CPManager.CPManagerObject[0]
    cp0 = cpmgr0.ControlPointList.ControlPoint[0]
    assert(
        pfPlanTrial_0.Trial[0].Name,
        pfPlanTrial_0.Trial[0].PrescriptionList.Prescription[0].PrescriptionDose,
        pfPlanTrial_0.Trial[0].BeamList.Beam[0].Name,
        pfPlanTrial_0.Trial[0].BeamList.Beam[0].Bolus.Type,
        pfPlanTrial_0.Trial[0].BeamList.Beam[0].Compensator.Name,
        pfPlanTrial_0.Trial[0].BeamList.Beam[3].MonitorUnitInfo.PrescriptionDose
    ) == (
        'sMLC',
        4250.0,
        'Med Lt Brst',
        'No bolus',
        '',
        39.8437
    )

def test0_PFPlanTrial_CP():
    cpmgr0 = pfPlanTrial_0.Trial[0].BeamList.Beam[0].CPManager.CPManagerObject[0]
    cp0 = cpmgr0.ControlPointList.ControlPoint[0]
    assert(
        cpmgr0.NumberOfControlPoints,
        cpmgr0.JawsConformance,
        cp0.Gantry,
        cp0.WedgeContext.WedgeName,
        cp0.MLCLeafPositions.RawData.NumberOfPoints,
        cp0.MLCLeafPositions.RawData.Points[27]
    ) == (
        4,
        'Static',
        306.0,
        'No Wedge',
        60,
        8.2
    )

def test0_PFPlanTrial_BM():
    cpmgr0 = pfPlanTrial_0.Trial[0].BeamList.Beam[0].CPManager.CPManagerObject[0]
    cp0 = cpmgr0.ControlPointList.ControlPoint[0]
    bm0 = cp0.ModifierList.BeamModifier[0]
    assert(
        bm0.Name,
        bm0.ContourList.CurvePainter[0].Curve.RawData.NumberOfDimensions,
        bm0.ContourList.CurvePainter[0].Curve.RawData.Points[1],
        bm0.ContourList.CurvePainter[0].Curve.RawData.Points[23]
    ) == (
        'BeamModifier_1',
        2,
        -10.5667,
        -10.3606
    )


Pdict = readPFile(prjpath+'examples/Patient_6204/Plan_1/plan.Trial', 
                'plan.Trial', 'dict')
pfPlanTrial_1 = PFPlanTrial(**Pdict)

def test1_PFPlanTrial():
    cpmgr0 = pfPlanTrial_1.Trial[0].BeamList.Beam[0].CPManager.CPManagerObject[0]
    cp0 = cpmgr0.ControlPointList.ControlPoint[0]
    assert(
        pfPlanTrial_1.Trial[0].Name,
        pfPlanTrial_1.Trial[0].PrescriptionList.Prescription[0].PrescriptionDose,
        pfPlanTrial_1.Trial[0].BeamList.Beam[0].Name,
        pfPlanTrial_1.Trial[0].BeamList.Beam[0].Bolus.Type,
        pfPlanTrial_1.Trial[0].BeamList.Beam[0].Compensator.Name,
        pfPlanTrial_1.Trial[0].BeamList.Beam[0].MonitorUnitInfo.PrescriptionDose
    ) == (
        'Direct Electron',
        1250.0,
        'E Bst Lt Brst',
        'No bolus',
        '',
        263.158
    )

def test1_PFPlanTrial_CP():
    cpmgr0 = pfPlanTrial_1.Trial[0].BeamList.Beam[0].CPManager.CPManagerObject[0]
    cp0 = cpmgr0.ControlPointList.ControlPoint[0]
    assert(
        cpmgr0.NumberOfControlPoints,
        cpmgr0.JawsConformance,
        cp0.Gantry,
        cp0.WedgeContext.WedgeName,
        cp0.MLCLeafPositions.RawData.NumberOfPoints,
        cp0.MLCLeafPositions.RawData.Points[27]
    ) == (
        1,
        'Static',
        90.0,
        'No Wedge',
        60,
        3.0
    )

def test1_PFPlanTrial_BM():
    cpmgr0 = pfPlanTrial_1.Trial[0].BeamList.Beam[0].CPManager.CPManagerObject[0]
    cp0 = cpmgr0.ControlPointList.ControlPoint[0]
    bm0 = cp0.ModifierList.BeamModifier[0]
    assert(
        bm0.Name,
        bm0.ContourList.CurvePainter
    ) == (
        'BeamModifier_1',
        None
    )

