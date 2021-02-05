import os
import sys
from datetime import datetime
from typing import (List, Optional)
from pydantic import BaseModel
import logging
from pftools.readPFile import readPFile
from pftools.PFObjectVersion import _ObjectVersion

class PFPlanPatientSetup(BaseModel):
    Position = ''
    Orientation = ''
    TableMotion = ''
    ProductionLevel: Optional[int]
    ObjectVersion: Optional[_ObjectVersion] = None

def readPlanPatientSetup(pfpath, planid=0):
    fname = '%s/Plan_%s/plan.PatientSetup' % (pfpath, planid)
    pdict = readPFile(fname, 'plan.PatientSetup', 'dict')
    pfObj = PFPlanPatientSetup(**pdict)
    return pfObj


if __name__ == '__main__':
    prjpath = os.path.dirname(os.path.abspath(__file__))+'/../'

    FORMAT = "[%(asctime)s %(levelname)s - %(funcName)s] %(message)s"
    logging.basicConfig(format=FORMAT, filename=prjpath+'logs/test.log', 
                        level=logging.INFO)

    logging.info('Project foler is %s' % os.path.abspath(prjpath))

    # Patient
    Pdict = readPFile(prjpath+'examples/Patient_6204/Plan_0/plan.PatientSetup', 
                    'plan.PatientSetup', 'dict')
    #print(Pdict)
    #print(len(Pdict))
    pfPlanPtSetup = PFPlanPatientSetup(**Pdict)

    print(pfPlanPtSetup.Orientation)