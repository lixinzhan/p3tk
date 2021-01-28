import os
import sys
from datetime import datetime
from typing import (List, Optional)
from pydantic import BaseModel
import logging
from readPFile import readPFile

class _Curve(BaseModel):
    blocksize: Optional[float]
    num_points: Optional[int]
    points: Optional[List] = []

class _ROI(BaseModel):
    name: str
    density: Optional[float]
    density_units: Optional[str] = ''
    num_curve: Optional[int]
    curve: List[_Curve]

class PFPlanROI(BaseModel):
    roi: List[_ROI] = None

if __name__ == '__main__':
    prjpath = os.path.dirname(os.path.abspath(__file__))+'/../'

    FORMAT = "[%(asctime)s %(levelname)s - %(funcName)s] %(message)s"
    logging.basicConfig(format=FORMAT, filename=prjpath+'logs/test.log', 
                        level=logging.INFO)

    logging.info('Project foler is %s' % os.path.abspath(prjpath))

    # Patient
    Pdict = readPFile(prjpath+'examples/Patient_6204/Plan_0/plan.roi', 
                    'plan.roi', 'dict')
    #print(Pdict)
    #print(len(Pdict))
    pfPlanRoi = PFPlanROI(**Pdict)

    print(pfPlanRoi.roi[1].name)
    print(pfPlanRoi.roi[0].num_curve)
    print(pfPlanRoi.roi[0].curve[0].num_points)
    print(pfPlanRoi.roi[0].curve[0].points[7])
