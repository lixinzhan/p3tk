import os
import sys
import logging
from pftools.PFImgInfo import PFImgInfo
from pftools.PFBackup import PFBackup

from pydicom.dataset import Dataset
from pydicom.dataset import FileDataset
from pydicom.dataset import FileMetaDataset

class PFDicom():
    def __init__(self,pfpath) -> None :
        logging.info('Start reading in Pinnacle backup files from folder %s\n' % pfpath)
        self.PFBackup = PFBackup(pfpath)
        logging.info('Reading Pinnacle backup files DONE!')

        self.Preamble = b'0' * 128
        self.Prefix = 'DICM'

        logging.info('Setting file meta information ...')
        self.FileMeta = FileMetaDataset()
        # CT Image Storage
        self.FileMeta.MediaStorageSOPClassUID = '1.2.840.10008.5.1.4.1.1.2'
        self.FileMeta.MediaStorageSOPInstanceUID = "1.2.3"
        self.FileMeta.ImplementationClassUID = "1.2.3.4"
        # Explicit VR Little Endian
        self.FileMeta.TransferSyntaxUID = '1.2.840.10008.1.2.1'

if __name__ == '__main__':
    prjpath = os.path.dirname(os.path.abspath(__file__))+'/../'

    FORMAT = "[%(asctime)s %(levelname)s - %(funcName)s] %(message)s"
    logging.basicConfig(format=FORMAT, filename=prjpath+'logs/test.log', level=logging.INFO)

    print('Start creating DICOM Files ...')
