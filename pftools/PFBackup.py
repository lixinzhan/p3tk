import os
from tests.test_pfread import PlanInfo, PlanPoints
from typing import (Optional, List)
import sys
from datetime import datetime
import logging

from pftools.readPFile import readPFile
from pftools.PFImgInfo import PFImgInfo
from pftools.PFImgSetHeader import PFImgSetHeader
from pftools.PFPatient import PFPatient
from pftools.PFPlanPatientSetup import PFPlanPatientSetup
from pftools.PFPlanInfo import PFPlanInfo
from pftools.PFPlanPoints import PFPlanPoints
from pftools.PFPlanROI import PFPlanROI
from pftools.PFPlanTrial import PFPlanTrial

class _ImageSet():
    def __init__(self) -> None:
        self.Header: Optional[PFImgSetHeader] = None
        self.ImageInfoList: Optional[PFImgInfo] = None
        self.ImageSetID: Optional[int] = 0

class _PPlan():
    def __init__(self) -> None:        
        self.PlanPatientSetup: Optional[PFPlanPatientSetup] = None
        self.PlanInfo: Optional[PFPlanInfo] = None
        self.PlanPoints: Optional[PFPlanPoints] = None
        self.PlanROI: Optional[PFPlanROI] = None
        self.PlanTrial: Optional[PFPlanTrial] = None
        self.PlanID: Optional[int] = 0

class PFBackup():
    def __init__(self, ptpath) -> None:
        fname = '%s/Patient' % ptpath
        pfdict = readPFile(fname, 'Patient', 'dict')
        self.Patient = PFPatient(**pfdict)

        self.NumberOfImageSets = len(self.Patient.ImageSetList.ImageSet)
        self.NumberOfPlans = len(self.Patient.PlanList.Plan)

        imgsetID = []
        for iset in self.Patient.ImageSetList.ImageSet:
            imgsetID.append(iset.ImageSetID)
        planID = []
        for plan in self.Patient.PlanList.Plan:
            planID.append(plan.PlanID)

        self.ImageSet: List[_ImageSet] = []
        for id in imgsetID:
            imgset = _ImageSet()
            imgset.ImageSetID = id

            # obtain header
            fname = '%s/ImageSet_%s.header' % (ptpath, id)
            pfdict = readPFile(fname, 'ImageSet.header', 'dict')
            imgset.Header = PFImgSetHeader(**pfdict)

            # obtain info for all slices
            fname = '%s/ImageSet_%s.ImageInfo' % (ptpath, id)
            pfdict = readPFile(fname, 'ImageSet.ImageInfo', 'dict')
            imgset.ImageInfoList = PFImgInfo(**pfdict)

            self.ImageSet.append(imgset)
            print('Reading ImageSet_%s done.'%id)

        self.Plan: List[_PPlan] = []
        for id in planID:
            pplan = _PPlan()
            pplan.PlanID = id

            # PlanPatientSetup
            fname = '%s/Plan_%s/plan.PatientSetup' % (ptpath, id)
            pfdict = readPFile(fname, 'plan.PatientSetup', 'dict')
            pplan.PlanPatientSetup = PFPlanPatientSetup(**pfdict)

            # PlanInfo
            fname = '%s/Plan_%s/plan.PlanInfo' % (ptpath, id)
            pfdict = readPFile(fname, 'plan.PlanInfo', 'dict')
            pplan.PlanInfo = PFPlanInfo(**pfdict)

            # PlanPoints
            fname = '%s/Plan_%s/plan.Points' % (ptpath, id)
            pfdict = readPFile(fname, 'plan.Points', 'dict')
            pplan.PlanPoints = PFPlanPoints(**pfdict)

            # PlanROI
            fname = '%s/Plan_%s/plan.roi' % (ptpath, id)
            pfdict = readPFile(fname, 'plan.roi', 'dict')
            pplan.PlanROI = PFPlanROI(**pfdict)

            # PlanTrial
            fname = '%s/Plan_%s/plan.Trial' % (ptpath, id)
            pfdict = readPFile(fname, 'plan.Trial', 'dict')
            pplan.PlanTrial = PFPlanTrial(**pfdict)

            self.Plan.append(pplan)
            print('Reading Plan_%s done.'%id)


if __name__ == '__main__':
    prjpath = os.path.dirname(os.path.abspath(__file__))+'/../'

    FORMAT = "[%(asctime)s %(levelname)s - %(funcName)s] %(message)s"
    logging.basicConfig(format=FORMAT, filename=prjpath+'logs/test.log', level=logging.INFO)

    logging.info('Project foler is %s' % os.path.abspath(prjpath))

    pfBackup = PFBackup(prjpath+'examples/Patient_6204')

    print(pfBackup.Patient.MedicalRecordNumber)
    print(pfBackup.ImageSet[0].Header.z_dim)
    print(pfBackup.ImageSet[0].ImageSetID)
    print(pfBackup.ImageSet[0].ImageInfoList.ImageInfo[0].SliceNumber)
    print(pfBackup.Plan[0].PlanTrial.Trial.Name)
    print(pfBackup.Plan[0].PlanID)
    print(pfBackup.Plan[1].PlanTrial.Trial.Name)
    print(pfBackup.Plan[1].PlanID)    