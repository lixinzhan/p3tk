import os
import sys
from datetime import datetime
from typing import (List, Optional)
from pydantic import BaseModel
import logging
from pftools.readPFile import readPFile

class PFImageSetInfo(BaseModel):
    ImageSetID: int
    PatientID = ''
    ImageName = ''
    NameFromScanner = ''
    ExamID = ''
    StudyID = ''
    Modality = ''
    NumberOfImages: Optional[int] = 0
    ScanTimeFromScanner = ''
    FileName = ''

def readImageSetInfo(pfpath, imgsetid):
    fname = '%s/Plan_%s/plan.ImageSet' % (pfpath, imgsetid)
    pdict = readPFile(fname, 'plan.ImageSet', 'dict')
    pfObj = PFImageSetInfo(**pdict)
    return pfObj


if __name__ == '__main__':
    prjpath = os.path.dirname(os.path.abspath(__file__))+'/../'

    FORMAT = "[%(asctime)s %(levelname)s - %(funcName)s] %(message)s"
    logging.basicConfig(format=FORMAT, filename=prjpath+'logs/test.log', 
                        level=logging.INFO)

    logging.info('Project foler is %s' % os.path.abspath(prjpath))

    # Patient
    Pdict = readPFile(prjpath+'examples/Patient_6204/ImageSet_0.ImageSet', 
                    'ImageSet.ImageSet', 'dict')
    #print(Pdict)
    #print(len(Pdict))
    pfImageSetInfo = PFImageSetInfo(**Pdict)

    print(pfImageSetInfo.NumberOfImages)