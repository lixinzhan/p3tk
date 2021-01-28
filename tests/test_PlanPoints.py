import os
import pytest
import logging
from pftools.PFPlanPoints import PFPlanPoints
from pftools.readPFile import readPFile

prjpath = os.path.dirname(os.path.abspath(__file__))+'/../'
FORMAT = "[%(asctime)s %(levelname)s - %(funcName)s] %(message)s"
logging.basicConfig(format=FORMAT, filename=prjpath+'logs/pytest.log', level=logging.WARNING)

Pdict = readPFile(prjpath+'examples/Patient_6204/Plan_0/plan.Points', 
                'plan.Points', 'dict')
pfPlanPt_0 = PFPlanPoints(**Pdict)

Pdict = readPFile(prjpath+'examples/Patient_6204/Plan_1/plan.Points', 
                'plan.Points', 'dict')
pfPlanPt_1 = PFPlanPoints(**Pdict)

def test0_PlanPoints():
    assert(pfPlanPt_0.Poi[0].Name,
            pfPlanPt_0.Poi[0].CoordinateFormat,
            pfPlanPt_0.Poi[0].ZCoord
        ) == (
            'CT REF',
            '%6.2f',
            -15.5688
        )

def test1_PlanPoints():
    assert(pfPlanPt_1.Poi[0].Name,
            pfPlanPt_1.Poi[0].CoordinateFormat,
            pfPlanPt_1.Poi[0].ZCoord
        ) == (
            'CT REF',
            '%6.2f',
            -15.5688
        )