import os
import sys
import logging
from pftools.PFImgInfo import PFImgInfo
from pftools.PFBackup import PFBackup

from pydicom import Dataset
from pydicom import FileDataset
from pydicom import FileMetaDataset

class PFDicom():
    def __init__(self,pfpath) -> None :
        logging.info('Start reading in Pinnacle backup files from folder %s\n' % pfpath)
        self.PFBackup = PFBackup(pfpath)
        logging.info('Reading Pinnacle backup files DONE!')

        logging.info('Setting file meta information ...')
        self.FileMeta = FileMetaDataset()


if __name__ == '__main__':
    prjpath = os.path.dirname(os.path.abspath(__file__))+'/../'

    FORMAT = "[%(asctime)s %(levelname)s - %(funcName)s] %(message)s"
    logging.basicConfig(format=FORMAT, filename=prjpath+'logs/test.log', level=logging.INFO)

    print('Start creating DICOM Files ...')
