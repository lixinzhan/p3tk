import os
import pytest
import logging
from pftools.PFPlanROI import PFPlanROI
from pftools.readPFile import readPFile

prjpath = os.path.dirname(os.path.abspath(__file__))+'/../'
FORMAT = "[%(asctime)s %(levelname)s - %(funcName)s] %(message)s"
logging.basicConfig(format=FORMAT, filename=prjpath+'logs/pytest.log', level=logging.WARNING)

Pdict = readPFile(prjpath+'examples/Patient_6204/Plan_0/plan.roi', 
                'plan.roi', 'dict')
pfPlanRoi_0 = PFPlanROI(**Pdict)

Pdict = readPFile(prjpath+'examples/Patient_6204/Plan_1/plan.roi', 
                'plan.roi', 'dict')
pfPlanRoi_1 = PFPlanROI(**Pdict)


def test0_PFPlanROI():
    assert(pfPlanRoi_0.roi[1].name,
            pfPlanRoi_0.roi[0].num_curve,
            pfPlanRoi_0.roi[0].curve[0].num_points,
            pfPlanRoi_0.roi[0].curve[0].points[7]
        ) == (
            'boost',
            11,
            49,
            -67.9697
        )

def test1_PFPlanROI():
    assert(pfPlanRoi_1.roi[1].name,
            pfPlanRoi_1.roi[0].num_curve,
            pfPlanRoi_1.roi[0].curve[0].num_points,
            pfPlanRoi_1.roi[0].curve[0].points[7]
        ) == (
            'boost',
            11,
            49,
            -67.9697
        )
