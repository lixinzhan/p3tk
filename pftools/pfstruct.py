import os
import sys
import logging
from pftools.readPFile import readPFile

class PBKStruct():
    def __init__(self, pbkfolder) -> None:
        '''
        Read in the Patient Backup folder.
        Folder Structure should be generally as below:
        .../Institution_##/Mount_0/Patient_####
            Patient
            ImageSet_#.ImageInfo
            ImageSet_#.ImageSet
            ImageSet_#.header
            ImageSet_#.img
            ImageSet_#.DICOM
                ... a list of dicom CT slice files ...
            Plan_#:
                plan.PatientSetup
                plan.Pinnacle.Machines
                plan.PlanInfo
                plan.Points
                plan.Trial
                Plan.Trial.binary.###
                plan.defaults
                plan.roi

        '''

        if not os.path.exists(pbkfolder):
            logging.error('Pinnacle Backup Folder does not exist!')
            return
        
        # Read in patient information first
        if not os.path.exists('%s/Patient'%pbkfolder):
            logging.error('Patient file does not exist.')
            return
        self.Patient = readPFile('%s/Patient'%pbkfolder, 'Patient')
        self.ImageSets = self.Patient.ImageSetList.ImageSet
        self.Plans = self.Patient.PlanList.Plan
        for iset in range(len(self.ImageSets)):
            # read in ImageInfo for each ImageSet and append to ImageSets/Patient)
            id = self.ImageSets[iset].ImageSetID
            ImageInfo = readPFile('%s/ImageSet_%s.ImageInfo'%(pbkfolder,id), 'ImageSet.ImageInfo')
            self.ImageSets[iset].ImageInfoList = ImageInfo

            # read in header for each ImageSet and append to ImageSets/Patient
            Header = readPFile('%s/ImageSet_%s.header'%(pbkfolder,id), 'ImageSet.header')
            self.ImageSets[iset].Header = Header
        
if __name__ == "__main__":
    prjpath = os.path.dirname(os.path.abspath(__file__))+'/../'

    FORMAT = "[%(asctime)s %(levelname)s - %(funcName)s] %(message)s"
    logging.basicConfig(format=FORMAT, filename=prjpath+'logs/test.log', level=logging.INFO)

    pbk = PBKStruct('%s/examples/Patient_6204'%prjpath)

    print(pbk.Patient.MedicalRecordNumber)
    print(pbk.ImageSets[0].ImageSetID, pbk.ImageSets[0].NumberOfImages)
    print(pbk.ImageSets[0].ImageInfoList.ImageInfo[1].SliceNumber)
    print(pbk.ImageSets[0].Header.x_dim)
    
