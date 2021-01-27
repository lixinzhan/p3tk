import os
import sys
from pydantic import BaseModel

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
    ImageSetList: Optional[_ImageSet] = []
    PlanList: Optional[_Plan] = []

class _ImageSet(BaseModel):
    ImageSetID: int
    ImageName = ''
    ExamID = ''
    StudyID = ''
    Modality = ''
    NumberOfImages = 0
    ScanTimeFromScanner: Optional[datetime] = None

class __Plan(BaseModel):
    PlanID: int
    PlanName = ''
    PrimaryCTImageSetID = -1
    PrimaryImageType = ''
