import os
import sys
from datetime import datetime
from typing import (List, Optional)
from pydantic import BaseModel
import logging
from readPFile import readPFile

class _POI(BaseModel):
    Name: str
    XCoord: Optional[float]
    YCoord: Optional[float]
    ZCoord: Optional[float]
    XRotation: Optional[float]
    YRotation: Optional[float]
    ZRotation: Optional[float]
    CoordSys = ''
    CoordinateFormat = ''

class PFPlanPoints(BaseModel):
    Poi: List[_POI] = None

if __name__ == '__main__':
    prjpath = os.path.dirname(os.path.abspath(__file__))+'/../'

    FORMAT = "[%(asctime)s %(levelname)s - %(funcName)s] %(message)s"
    logging.basicConfig(format=FORMAT, filename=prjpath+'logs/test.log', 
                        level=logging.INFO)

    logging.info('Project foler is %s' % os.path.abspath(prjpath))

    # Patient
    Pdict = readPFile(prjpath+'examples/Patient_6204/Plan_0/plan.Points', 
                    'plan.Points', 'dict')
    #print(Pdict)
    #print(len(Pdict))
    pfPlanPt = PFPlanPoints(**Pdict)

    print(pfPlanPt.Poi[1].Name)
    print(pfPlanPt.Poi[2].CoordinateFormat)
    print(pfPlanPt.Poi[0].ZCoord)
