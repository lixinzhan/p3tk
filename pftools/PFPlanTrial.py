import os
import sys
from datetime import datetime
from typing import (Dict, List, Optional)
from pydantic import BaseModel
import logging

from pftools.readPFile import readPFile
from pftools.PFObjectVersion import _ObjectVersion

class _RawData(BaseModel):
    NumberOfDimensions: Optional[int]
    NumberOfPoints: Optional[int]
    Points: Optional[List] = []

class _Curve(BaseModel):
    RawData: Optional[_RawData] = None

class _CurvePainter(BaseModel):
    Curve: Optional[_Curve] = None
    SliceCoordinate: Optional[float]
    Orientation = ''

class _ContourList(BaseModel):
    CurvePainter: List[_CurvePainter] = None

class _BeamModifier(BaseModel):
    Name = ''
    FixToCollimator: Optional[int]
    AutoBlock: Optional[int]
    StructureToBlock = ''
    Margin: Optional[float]
    InsideMode = ''
    OutsideMode = ''
    ContourList: Optional[_ContourList] = None

class _ModifierList(BaseModel):
    BeamModifier: List[_BeamModifier] = None

class _WedgeContext(BaseModel):
    WedgeName = ''
    Orientation = ''
    OffsetOrigin = ''
    OffsetDistance: Optional[float]
    Angle = ''
    MinDeliverableMU = 0
    MaxDeliverableMU = 1e+30

class _MLCLeafPositions(BaseModel):
    RawData: Optional[_RawData] = None

class _ControlPoint(BaseModel):
    Gantry: Optional[float]
    Couch: Optional[float]
    Collimator: Optional[float]
    LeftJawPosition: Optional[float]
    RightJawPosition: Optional[float]
    TopJawPosition: Optional[float]
    BottomJawPosition: Optional[float]
    Weight: Optional[float]
    WeightLocked: Optional[int]
    PercentOfArc: Optional[float]
    HasSharedModifierList: Optional[int]
    WedgeContext: Optional[_WedgeContext] = None
    ModifierList: Optional[_ModifierList] = None
    MLCLeafPositions: Optional[_MLCLeafPositions] = None

class _ControlPointList(BaseModel):
    ControlPoint: List[_ControlPoint]

class _CPManagerObject(BaseModel):
    NumberOfControlPoints: Optional[int]
    ControlPointList: Optional[_ControlPointList] = None
    GantryIsCCW: Optional[int]
    MLCPushMethod = ''
    JawsConformance = ''

class _CPManager(BaseModel):
    CPManagerObject: List[_CPManagerObject] = None

class _MonitorUnitInfo(BaseModel):
    PrescriptionDose: Optional[float]
    SourceToPrescriptionPointDistance: Optional[float]
    TotalTransmissionFraction: Optional[float]
    TransmissionDescription = ''
    PrescriptionPointDepth: Optional[float]
    PrescriptionPointRadDepth: Optional[float]
    DepthToActualPoint: Optional[float]
    SSDToActualPoint: Optional[float]
    RadDepthToActualPoint: Optional[float]
    PrescriptionPointRadDepthValid: Optional[int]
    PrescriptionPointOffAxisDistance: Optional[float]
    NormalizedDose: Optional[float]
    OffAxisRatio: Optional[float]
    CollimatorOutputFactor: Optional[float]
    RelativeOutputFactor: Optional[float]
    PhantomOutputFactor: Optional[float]
    OFMeasurementDepth: Optional[float]
    OutputFactorInfo = ''

class _Bolus(BaseModel):
    Type = ''
    Density: Optional[float]
    Thickness: Optional[float]

class _Compensator(BaseModel):
    Name = ''

class _Prescription(BaseModel):
    Name = ''
    RequestedMonitorUnitsPerFraction: Optional[float]
    PrescriptionDose: float
    PrescriptionPercent: Optional[float]
    NumberOfFractions: int
    PrescriptionPoint = ''
    Method = ''
    NormalizationMethod = ''
    PrescriptionPeriod = ''
    WeightsProportionalTo = ''

class _PrescriptionList(BaseModel):
    Prescription: List[_Prescription] = None

class _Beam(BaseModel):
      Name: str
      IsocenterName = ''
      PrescriptionName = ''
      UsePoiForPrescriptionPoint: Optional[int]
      PrescriptionPointName = ''
      PrescriptionPointDepth: Optional[float]
      PrescriptionPointXOffset: Optional[float]
      PrescriptionPointYOffset: Optional[float]
      SpecifyDosePerMuAtPrescriptionPoint: Optional[float]
      DosePerMuAtPrescriptionPoint: Optional[float]
      MachineNameAndVersion = ''
      Modality = ''
      MachineEnergyName = ''
      SetBeamType = ''
      CPManager: Optional[_CPManager]
      IMRTFilter = ''
      IMRTWedge = ''
      IMRTDirection = ''
      IMRTParameterType = ''
      PrevIMRTParameterType = ''
      UseMLC: Optional[int]
      DynamicBlocks: Optional[int]
      CircularFieldDiameter: Optional[float]
      ElectronApplicatorName = ''
      SSD: Optional[float]
      AvgSSD: Optional[float]
      SSDValid: Optional[int]
      LeftAutoSurroundMargin: Optional[float]
      RightAutoSurroundMargin: Optional[float]
      TopAutoSurroundMargin: Optional[float]
      BottomAutoSurroundMargin: Optional[float]
      AutoSurround: Optional[int]
      OpenExtraLeafPairs: Optional[int]
      BlockingMaskPixelSize: Optional[float]
      BlockingMaskCutoffArea: Optional[float]
      BlockAndTrayFactor: Optional[float]
      TrayNumber = ''
      BlockJawOverlap: Optional[float]
      TrayFactor: Optional[float]
      Bolus: Optional[_Bolus] = None
      Compensator: Optional[_Compensator] = None
      CompensatorScaleFactor: Optional[float]
      ComputationVersion = ''
      MonitorUnitInfo: Optional[_MonitorUnitInfo] = None
      DoseVolume = ''

      # added extra Prescription property for easy link
      Prescription: Optional[_Prescription] = None
      # flag to be used for removing extra beams
      Removable = False


class _BeamList(BaseModel):
    Beam: List[_Beam] = None

class _Trial(BaseModel):
    Name: str
    CtToDensityName = ''
    CtToDensityVersion = ''
    DoseGridVoxelSizeX: float
    DoseGridVoxelSizeY: float
    DoseGridVoxelSizeZ: float
    DoseGridDimensionX: int
    DoseGridDimensionY: int
    DoseGridDimensionZ: int
    DoseGridOriginX: float
    DoseGridOriginY: float
    DoseGridOriginZ: float
    DoseStartSlice: Optional[int]
    DoseEndSlice: Optional[int]
    PrescriptionList: Optional[_PrescriptionList] = None
    BeamList: Optional[_BeamList]
    ObjectVersion: Optional[_ObjectVersion] = None

    # added in items
    Removable = False
    TrialID: Optional[int]

class PFPlanTrial(BaseModel):
    Trial: List[_Trial] = None

def readPlanTrial(pfpath, planid=0):
    fname = '%s/Plan_%s/plan.Trial' % (pfpath, planid)
    pdict = readPFile(fname, 'plan.Trial', 'dict')
    pfObj = PFPlanTrial(**pdict)
    return pfObj


if __name__ == '__main__':
    prjpath = os.path.dirname(os.path.abspath(__file__))+'/../'

    FORMAT = "[%(asctime)s %(levelname)s - %(funcName)s] %(message)s"
    logging.basicConfig(format=FORMAT, filename=prjpath+'logs/test.log', 
                        level=logging.INFO)

    logging.info('Project foler is %s' % os.path.abspath(prjpath))

    # Patient
    Pdict = readPFile(prjpath+'examples/Patient_6204/Plan_0/plan.Trial', 
                    'plan.Trial', 'dict')
    #print(Pdict)
    #print(len(Pdict))
    pfPlanTrial = PFPlanTrial(**Pdict)

    ntrial = len(pfPlanTrial.Trial)
    print('Number of Trials: %s' % ntrial)

    for i in range(ntrial):
        print(pfPlanTrial.Trial[i].Name)
        print(pfPlanTrial.Trial[i].PrescriptionList.Prescription[0].PrescriptionDose)
        print(pfPlanTrial.Trial[i].BeamList.Beam[0].Name)
        cpmgr0 = pfPlanTrial.Trial[i].BeamList.Beam[0].CPManager.CPManagerObject[0]
        print(cpmgr0.NumberOfControlPoints)
        print(cpmgr0.ControlPointList.ControlPoint[0].Gantry)
        print(cpmgr0.ControlPointList.ControlPoint[0].WedgeContext.WedgeName)
        cp0 = cpmgr0.ControlPointList.ControlPoint[0]
        print(cp0.ModifierList.BeamModifier[0].Name)
        print(cp0.ModifierList.BeamModifier[0].ContourList.CurvePainter[0].Curve.RawData.NumberOfPoints)
        print(cp0.ModifierList.BeamModifier[0].ContourList.CurvePainter[0].Curve.RawData.Points[1])
        print(cp0.ModifierList.BeamModifier[0].ContourList.CurvePainter[0].Curve.RawData.Points[23])
        print(cp0.MLCLeafPositions.RawData.NumberOfPoints)
        print(cp0.MLCLeafPositions.RawData.Points[27])
        print(cpmgr0.JawsConformance)
        print(pfPlanTrial.Trial[i].BeamList.Beam[0].Bolus.Type)
        print(pfPlanTrial.Trial[i].BeamList.Beam[0].Compensator.Name)    
        print(pfPlanTrial.Trial[i].BeamList.Beam[3].MonitorUnitInfo.PrescriptionDose)
