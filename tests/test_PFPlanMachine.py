import os
import pytest
import logging
from pftools.PFPlanMachine import readMachine
# from pftools.readPFile import readPFile

prjpath = os.path.dirname(os.path.abspath(__file__))+'/../'
FORMAT = "[%(asctime)s %(levelname)s - %(funcName)s] %(message)s"
logging.basicConfig(format=FORMAT, filename=prjpath+'logs/pytest.log', level=logging.WARNING)

pfMachine = readMachine(prjpath+'examples/Patient_6204/', planid=0)

def test0_PFPlanMachine():
    assert( pfMachine.Machine[0].PhotonEnergyList.MachineEnergy[0].Name, 
            pfMachine.Machine[0].PhotonEnergyList.MachineEnergy[0].PhysicsData.OutputFactor.DosePerMuAtCalibration, 
            pfMachine.Machine[0].PhotonEnergyList.MachineEnergy[1].Name, 
            pfMachine.Machine[0].PhotonEnergyList.MachineEnergy[1].PhysicsData.OutputFactor.DosePerMuAtCalibration, 
            pfMachine.Machine[0].ElectronEnergyList.MachineEnergy[0].Name,
            pfMachine.Machine[0].ElectronEnergyList.MachineEnergy[0].PhysicsData.OutputFactor.DosePerMuAtCalibration, 
            pfMachine.Machine[0].ElectronEnergyList.MachineEnergy[1].Name,
            pfMachine.Machine[0].ElectronEnergyList.MachineEnergy[1].PhysicsData.OutputFactor.DosePerMuAtCalibration, 
            pfMachine.Machine[0].ElectronEnergyList.MachineEnergy[2].Name,
            pfMachine.Machine[0].ElectronEnergyList.MachineEnergy[2].PhysicsData.OutputFactor.DosePerMuAtCalibration, 
            pfMachine.Machine[0].ElectronEnergyList.MachineEnergy[3].Name,
            pfMachine.Machine[0].ElectronEnergyList.MachineEnergy[3].PhysicsData.OutputFactor.DosePerMuAtCalibration, 
            pfMachine.Machine[0].ElectronEnergyList.MachineEnergy[4].Name,
            pfMachine.Machine[0].ElectronEnergyList.MachineEnergy[4].PhysicsData.OutputFactor.DosePerMuAtCalibration, 
        ) == (
            '6X',
            0.8401,
            '15X',
            0.8905,
            '6e',
            1.0,
            '9e',
            1.0,
            '12e',
            1.0,
            '16e',
            1.0,
            '4e',
            1.0
        )
        