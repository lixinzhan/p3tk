import os
import pytest
import logging
from pftools.PFBackup import PFBackup

prjpath = os.path.dirname(os.path.abspath(__file__))+'/../'
FORMAT = "[%(asctime)s %(levelname)s - %(funcName)s] %(message)s"
logging.basicConfig(format=FORMAT, filename=prjpath+'logs/pytest.log', level=logging.WARNING)

pfBackup = PFBackup(prjpath+'examples/Patient_6204')

def test0_PFPFBackup():
    assert(pfBackup.Patient.MedicalRecordNumber,
            pfBackup.ImageSet[0].Header.z_dim,
            pfBackup.ImageSet[0].ImageSetID,
            pfBackup.ImageSet[0].ImageInfoList.ImageInfo[0].SliceNumber
    ) == (
        '00003030',
        98,
        0,
        1
    )

def test1_PFBackup():
    assert(pfBackup.Plan[0].PlanTrial.Trial[0].Name,
            pfBackup.Plan[0].PlanID,
            pfBackup.Plan[1].PlanTrial.Trial[0].Name,
            pfBackup.Plan[1].PlanID
    ) == (
        'sMLC',
        0,
        'Direct Electron',
        1
    )
