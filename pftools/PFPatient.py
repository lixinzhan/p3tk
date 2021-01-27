import os
import sys
from datetime import datetime
from typing import (List, Optional)
from pydantic import BaseModel
import logging
from readPFile import readPFile

class _ImageSet(BaseModel):
    ImageSetID: int
    ImageName = ''
    ExamID = ''
    StudyID = ''
    Modality = ''
    NumberOfImages = 0
    ScanTimeFromScanner = ''

class _ImageSetList(BaseModel):
    ImageSet: List[_ImageSet] = None

class _Plan(BaseModel):
    PlanID: int
    PlanName = ''
    PrimaryCTImageSetID = -1
    PrimaryImageType = ''

class _PlanList(BaseModel):
    Plan: List[_Plan] = None

class PFPatient(BaseModel):
    LastName = ''
    FirstName = ''
    MiddleName = ''
    MedicalRecordNumber = ''
    RadiationOncologist = ''
    NextUniquePlanID = 0
    NextUniqueImageSetID = 0
    Gender = ''
    DateOfBirth = ''
    ImageSetList: Optional[_ImageSetList] = None
    PlanList: Optional[_PlanList] = None


if __name__ == '__main__':
    prjpath = os.path.dirname(os.path.abspath(__file__))+'/../'

    FORMAT = "[%(asctime)s %(levelname)s - %(funcName)s] %(message)s"
    logging.basicConfig(format=FORMAT, filename=prjpath+'logs/test.log', level=logging.INFO)

    logging.info('Project foler is %s' % os.path.abspath(prjpath))

    # Patient
    Pdict = readPFile(prjpath+'examples/Patient_6204/Patient', 'Patient', 'dict')
    #print(Pdict)
    #print(len(Pdict))
    pfPatient = PFPatient(**Pdict)

    print(pfPatient.MedicalRecordNumber)
    print(pfPatient.ImageSetList.ImageSet[0].NumberOfImages)
    print(pfPatient.ImageSetList.ImageSet[0].ScanTimeFromScanner)
    print(pfPatient.PlanList.Plan[1].PlanName)