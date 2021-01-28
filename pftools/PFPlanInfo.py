import os
import sys
from datetime import datetime
from typing import (List, Optional)
from pydantic import BaseModel
import logging
from pftools.readPFile import readPFile

class PFPlanInfo(BaseModel):
    PatientName = ''
    Institution = ''
    PlanName = ''
    Planner = ''
    LastName = ''
    FirstName = ''
    MiddleName = ''
    MedicalRecordNumber = ''
    Physician = ''
    Gender = ''
    DateOfBirth = ''

if __name__ == '__main__':
    prjpath = os.path.dirname(os.path.abspath(__file__))+'/../'

    FORMAT = "[%(asctime)s %(levelname)s - %(funcName)s] %(message)s"
    logging.basicConfig(format=FORMAT, filename=prjpath+'logs/test.log', 
                        level=logging.INFO)

    logging.info('Project foler is %s' % os.path.abspath(prjpath))

    # Patient
    Pdict = readPFile(prjpath+'examples/Patient_6204/Plan_0/plan.PlanInfo', 
                    'plan.PlanInfo', 'dict')
    #print(Pdict)
    #print(len(Pdict))
    pfPlanInfo = PFPlanInfo(**Pdict)

    print(pfPlanInfo.PlanName)