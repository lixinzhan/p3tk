import os
import sys
from datetime import datetime
from typing import (List, Optional)
from pydantic import BaseModel
import logging
from pftools.readPFile import readPFile

# class _CouchAngle(BaseModel):
#     Name = ''
#     TwelveOClockAngle: Optional[float]
#     ClockwiseIncreases: Optional[int]
#     NominalAngle: Optional[float]
#     MinimumAngle: Optional[float]
#     MaximumAngle: Optional[float]
#     DecimalPlaces: Optional[float]
#     CanBeArc: Optional[float]
#     RotationDirection = ''
#     ConformalArc: Optional[int]

# class _GantryAngle(BaseModel):
#     Name = ''
#     TwelveOClockAngle: Optional[float]
#     ClockwiseIncreases: Optional[int]
#     NominalAngle: Optional[float]
#     MinimumAngle: Optional[float]
#     MaximumAngle: Optional[float]
#     DecimalPlaces: Optional[float]
#     CanBeArc: Optional[float]
#     RotationDirection = ''
#     ConformalArc: Optional[int]
# class _CollimatorAngle(BaseModel):
#     Name = ''
#     TwelveOClockAngle: Optional[float]
#     ClockwiseIncreases: Optional[int]
#     NominalAngle: Optional[float]
#     MinimumAngle: Optional[float]
#     MaximumAngle: Optional[float]
#     DecimalPlaces: Optional[float]
#     CanBeArc: Optional[float]
#     RotationDirection = ''
#     ConformalArc: Optional[int]

# class _ElectronApplicator(BaseModel):
#     Name = ''
#     Width: Optional[float]
#     Length: Optional[float]
#     ManufacturerCode = ''
# class _ElectronApplicatorList(BaseModel):
#     ElectronApplicator: Optional[_ElectronApplicator] = None

class _Wedge(BaseModel):
    Name = ''
    SourceToWedgeDistance: Optional[float]
    NominalAngle: Optional[float]
    WedgeFactor: Optional[float]
    AttenuationCoefficient: Optional[float]
    IsDynamic: Optional[int]
    CanBeLeftToRight: Optional[int]
    CanBeRightToLeft: Optional[int]
    CanBeBottomToTop: Optional[int]
    CanBeTopToBottom: Optional[int]
    LeftToRightLabel = ''
    RightToLeftLabel = ''
    TopToBottomLabel = ''
    BottomToTopLabel = ''
    LeftToRightCode = ''
    RightToLeftCode = ''
    TopToBottomCode = ''
    BottomToTopCode = ''

class _WedgeList(BaseModel):
    Wedge: List[_Wedge] = None

# class _ElectronModel(BaseModel):
#     IncidentEnergy: Optional[float]

# class _PhotonModel(BaseModel):
#     Name = ''
#     Energy = ''

# class _PhotonModelList(BaseModel):
#     PhotonModel: List[_PhotonModel] = None

class _OutputFactor(BaseModel):
    ReferenceDepth: Optional[float]
    SourceToCalibrationPointDistance: Optional[float]
    ElectronSSDTolerance: Optional[float]
    DosePerMuAtCalibration: Optional[float]
    CalculatedCalibrationDose: Optional[float]
    CalculatedCalibrationDoseValid: Optional[int]

class _PhysicsData(BaseModel):
    # ElectronModel: Optional[_ElectronModel] = None
    # PhotonModelList: Optional[_PhotonModelList] = None
    OutputFactor: Optional[_OutputFactor] = None

class _MachineEnergy(BaseModel):
    Value: Optional[int]
    Id: Optional[int]
    Name = ''
    PhysicsData: Optional[_PhysicsData] = None

class _PhotonEnergyList(BaseModel):
    MachineEnergy: List[_MachineEnergy] = None

class _ElectronEnergyList(BaseModel):
    MachineEnergy: List[_MachineEnergy] = None

class _Machine(BaseModel):
    Name = ''
    MachineType = ''
    CommissionedForPhotons: Optional[int]
    CommissionedForElectrons: Optional[int]
    CommissionedForStereo: Optional[int]
    SAD: Optional[float]
    SourceToBlockTrayDistance: Optional[float]
    PhotonEnergyList: Optional[_PhotonEnergyList] = None
    ElectronEnergyList: Optional[_ElectronEnergyList] = None

    # CouchAngle: Optional[_CouchAngle] = None
    # GantryAngle: Optional[_GantryAngle] = None
    # CollimatorAngle: Optional[_CollimatorAngle] = None
    # ElectronApplicatorList: Optional[_ElectronApplicatorList] = None
    WedgeList: Optional[_WedgeList] = None

class PFMachine(BaseModel):
    Machine: List[_Machine] = None

def readMachine(pfpath, planid=0):
    fname = '%s/Plan_%s/plan.Pinnacle.Machines' % (pfpath, planid)
    pdict = readPFile(fname, 'plan.Machine', 'dict')
    pfObj = PFMachine(**pdict)
    return pfObj


if __name__ == '__main__':
    prjpath = os.path.dirname(os.path.abspath(__file__))+'/../'

    FORMAT = "[%(asctime)s %(levelname)s - %(funcName)s] %(message)s"
    logging.basicConfig(format=FORMAT, filename=prjpath+'logs/test.log', 
                        level=logging.INFO)

    logging.info('Project foler is %s' % os.path.abspath(prjpath))

    # Patient
    Pdict = readPFile(prjpath+'examples/Patient_6204/Plan_0/plan.Pinnacle.Machines', 
                    'plan.Machine', 'dict')
    # print(Pdict['Machine'][0]['PhotonEnergyList'] ) #['MachineEnergy'])
    pfMachine = PFMachine(**Pdict)

    print(pfMachine.Machine[0].MachineType)

    xenergy = pfMachine.Machine[0].PhotonEnergyList.MachineEnergy
    for xe in xenergy:
        print('Photon Energy: ', xe.Name)

    xenergy = pfMachine.Machine[0].ElectronEnergyList.MachineEnergy
    for xe in xenergy:
        print('Electron Energy: ', xe.Name)
