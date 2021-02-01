import os
import sys
from datetime import datetime
from typing import (List, Optional)
from pydantic import BaseModel
import logging
from pftools.readPFile import readPFile

class PFImgSetHeader(BaseModel):
    x_dim: int
    y_dim: int
    z_dim: int
    datatype: Optional[int]
    bitpix: Optional[int]
    bytes_pix: Optional[int]
    x_pixdim: float
    y_pixdim: float
    z_pixdim: float
    x_start: float
    y_start: float
    z_start: float
    id: Optional[int]
    date = ''
    patient_position = ''
    binary_header_size: Optional[int]
    manufacturer = ''
    model = ''
    couch_pos: Optional[float]
    couch_height: Optional[float]
    X_offset: Optional[float]
    Y_offset: Optional[float]
    dataset_modified = 0
    study_id: Optional[int]
    exam_id: Optional[int]
    patient_id = ''
    modality = ''

def readImageSetHeader(pfpath, imgsetid=0):
    fname = '%s/ImageSet_%s.header' % (pfpath, imgsetid)
    pdict = readPFile(fname, 'ImageSet.header', 'dict')
    pfObj = PFImgSetHeader(**pdict)
    return pfObj


if __name__ == '__main__':
    prjpath = os.path.dirname(os.path.abspath(__file__))+'/../'

    FORMAT = "[%(asctime)s %(levelname)s - %(funcName)s] %(message)s"
    logging.basicConfig(format=FORMAT, filename=prjpath+'logs/test.log', level=logging.INFO)

    logging.info('Project foler is %s' % os.path.abspath(prjpath))

    # Patient
    Pdict = readPFile(prjpath+'examples/Patient_6204/ImageSet_0.header', 'ImageSet.header', 'dict')

    pfImgSetHeader = PFImgSetHeader(**Pdict)

    #print(Pdict)

    print(pfImgSetHeader.z_dim)
    print(pfImgSetHeader.z_pixdim)
    print(pfImgSetHeader.patient_id)
    print(pfImgSetHeader.modality)


 