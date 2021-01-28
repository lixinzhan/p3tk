import os
import pytest
import logging
from pftools.PFImgSetHeader import PFImgSetHeader
from pftools.readPFile import readPFile

prjpath = os.path.dirname(os.path.abspath(__file__))+'/../'
FORMAT = "[%(asctime)s %(levelname)s - %(funcName)s] %(message)s"
logging.basicConfig(format=FORMAT, filename=prjpath+'logs/pytest.log', level=logging.WARNING)

Pdict = readPFile(prjpath+'examples/Patient_6204/ImageSet_0.header', 'ImageSet.header', 'dict')
pfImgSetHeader = PFImgSetHeader(**Pdict)

def test_PFImgSetHeader():
    assert(pfImgSetHeader.z_dim,
            pfImgSetHeader.z_pixdim,
            pfImgSetHeader.patient_id,
            pfImgSetHeader.modality
        ) == (
            98,
            0.3,
            '00003030',
            'CT'
        )

