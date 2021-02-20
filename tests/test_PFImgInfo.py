import os
import pytest
import logging
from pftools.PFImgInfo import PFImgInfo, readImageInfo
# from pftools.readPFile import readPFile

prjpath = os.path.dirname(os.path.abspath(__file__))+'/../'
FORMAT = "[%(asctime)s %(levelname)s - %(funcName)s] %(message)s"
logging.basicConfig(format=FORMAT, filename=prjpath+'logs/pytest.log', level=logging.WARNING)

# Pdict = readPFile(prjpath+'examples/Patient_6204/ImageSet_0.ImageInfo', 
#                 'ImageSet.ImageInfo', 'dict')
# pfImgInfo = PFImgInfo(**Pdict)

pfImgInfo = readImageInfo(prjpath+'examples/Patient_6204/', imgsetid=0)

def test_PFImgInfo():
    assert(pfImgInfo.ImageInfo[0].TablePosition,
            pfImgInfo.ImageInfo[1].SliceNumber,
            pfImgInfo.ImageInfo[97].InstanceUID
        ) == (
            -31.7688,
            2,
            '2.16.840.1.113662.2.12.0.3137.1168342749.1578'
        )

