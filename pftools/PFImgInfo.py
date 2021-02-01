import os
import sys
from datetime import datetime
from typing import (List, Optional)
from pydantic import BaseModel
import logging
from pftools.readPFile import readPFile

class _ImageInfo(BaseModel):
    SliceNumber: int
    TablePosition: Optional[float]
    CouchPos: Optional[float]
    SeriesUID: Optional[str] = ''
    StudyInstanceUID: Optional[str] = ''
    FrameUID: Optional[str] = ''
    ClassUID: Optional[str] = ''
    InstanceUID: Optional[str] = ''
    SUVScale: Optional[int] = 1
    ColorLUTScale: Optional[int] = 1

class PFImgInfo(BaseModel):
    ImageInfo: List[_ImageInfo] = None

def readImageInfo(pfpath, imgsetid=0):
    fname = '%s/ImageSet_%s.ImageInfo' % (pfpath, imgsetid)
    pdict = readPFile(fname, 'ImageSet.ImageInfo', 'dict')
    pfObj = PFImgInfo(**pdict)
    return pfObj


if __name__ == '__main__':
    prjpath = os.path.dirname(os.path.abspath(__file__))+'/../'

    FORMAT = "[%(asctime)s %(levelname)s - %(funcName)s] %(message)s"
    logging.basicConfig(format=FORMAT, filename=prjpath+'logs/test.log', 
                        level=logging.INFO)

    logging.info('Project foler is %s' % os.path.abspath(prjpath))

    # Patient
    Pdict = readPFile(prjpath+'examples/Patient_6204/ImageSet_0.ImageInfo', 
                    'ImageSet.ImageInfo', 'dict')
    #print(Pdict)
    pfImgInfo = PFImgInfo(**Pdict)

    print(pfImgInfo.ImageInfo[0].TablePosition)
    print(pfImgInfo.ImageInfo[1].SliceNumber)
    print(pfImgInfo.ImageInfo[97].InstanceUID)
