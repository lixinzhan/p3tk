import os
import pytest
import logging
from pftools.PFPatient import PFPatient
from pftools.readPFile import readPFile

prjpath = os.path.dirname(os.path.abspath(__file__))+'/../'
FORMAT = "[%(asctime)s %(levelname)s - %(funcName)s] %(message)s"
logging.basicConfig(format=FORMAT, filename=prjpath+'logs/pytest.log', level=logging.WARNING)

Pdict = readPFile(prjpath+'examples/Patient_6204/Patient', 'Patient', 'dict')
pfPatient = PFPatient(**Pdict)

def test_PFPatient():
    assert(pfPatient.MedicalRecordNumber,
            pfPatient.ImageSetList.ImageSet[0].NumberOfImages,
            pfPatient.ImageSetList.ImageSet[0].ScanTimeFromScanner,
            pfPatient.PlanList.Plan[1].PlanName
        ) == (
            '00003030',
            98,
            '2007-01-09',
            'LT BRST E BST'
        )