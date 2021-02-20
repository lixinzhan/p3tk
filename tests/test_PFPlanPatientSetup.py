import os
import pytest
import logging
from pftools.PFPlanPatientSetup import PFPlanPatientSetup, readPlanPatientSetup
# from pftools.readPFile import readPFile

prjpath = os.path.dirname(os.path.abspath(__file__))+'/../'
FORMAT = "[%(asctime)s %(levelname)s - %(funcName)s] %(message)s"
logging.basicConfig(format=FORMAT, filename=prjpath+'logs/pytest.log', level=logging.WARNING)

# Pdict = readPFile(prjpath+'examples/Patient_6204/Plan_0/plan.PatientSetup', 
#                 'plan.PatientSetup', 'dict')
# pfPlanPtSetup_0 = PFPlanPatientSetup(**Pdict)

# Pdict = readPFile(prjpath+'examples/Patient_6204/Plan_1/plan.PatientSetup', 
#                 'plan.PatientSetup', 'dict')
# pfPlanPtSetup_1 = PFPlanPatientSetup(**Pdict)

pfPlanPtSetup_0 = readPlanPatientSetup(prjpath+'examples/Patient_6204/', planid=0)
pfPlanPtSetup_1 = readPlanPatientSetup(prjpath+'examples/Patient_6204/', planid=1)

def test0_PFPlanPatientSetup():
    assert(pfPlanPtSetup_0.Orientation == 'Head First Into Scanner')

def test1_PFPlanPatientSetup():
    assert(pfPlanPtSetup_1.Orientation == 'Head First Into Scanner')