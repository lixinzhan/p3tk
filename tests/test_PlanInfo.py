import os
import pytest
import logging
from pftools.PFPlanInfo import PFPlanInfo, readPlanInfo
# from pftools.readPFile import readPFile

prjpath = os.path.dirname(os.path.abspath(__file__))+'/../'
FORMAT = "[%(asctime)s %(levelname)s - %(funcName)s] %(message)s"
logging.basicConfig(format=FORMAT, filename=prjpath+'logs/pytest.log', level=logging.WARNING)

# Pdict = readPFile(prjpath+'examples/Patient_6204/Plan_0/plan.PlanInfo', 
#                 'plan.PlanInfo', 'dict')
# pfPlanInfo_0 = PFPlanInfo(**Pdict)

# Pdict = readPFile(prjpath+'examples/Patient_6204/Plan_1/plan.PlanInfo', 
#                 'plan.PlanInfo', 'dict')
# pfPlanInfo_1 = PFPlanInfo(**Pdict)

pfPlanInfo_0 = readPlanInfo(prjpath+'examples/Patient_6204/', planid=0)
pfPlanInfo_1 = readPlanInfo(prjpath+'examples/Patient_6204/', planid=1)

def test0_PFPlanInfo():
    assert(pfPlanInfo_0.PlanName == 'LT BREAST')

def test1_PFPlanInfo():
    assert(pfPlanInfo_1.PlanName == 'LT BRST E BST')
