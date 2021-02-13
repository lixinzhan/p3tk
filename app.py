import os
import argparse
from pftools.PFDicom import PFDicom
import logging

if __name__ == '__main__':
    prjpath = os.path.dirname(os.path.abspath(__file__))
    FORMAT = "[%(asctime)s %(levelname)s - %(funcName)s] %(message)s"
    logging.basicConfig(format=FORMAT, filename=prjpath+'/logs/test.log', level=logging.INFO)

    parser = argparse.ArgumentParser(description='Create DICOM files from Pinnacle3 plan backups')
    parser.add_argument('-i', '--input', help='Backup patient path', required=True)
    parser.add_argument('-o', '--output', help='DICOM file saving location, default to current')
    parser.add_argument('-t', '--type', help='Output type: CT, RS, RP, RD or ALL, default to ALL')
    args = parser.parse_args()

    dcmdir  = ''
    dcmtype = 'ALL'
    dcmCT = False
    dcmRS = False
    dcmRP = False
    dcmRD = False

    ptdir = args.input
    if args.output:
        dcmdir = args.output
    if args.type:
        dcmtype = args.type

    if dcmtype == 'CT': 
        dcmCT = True
    elif dcmtype == 'RS': 
        dcmRS = True
    elif dcmtype == 'RP': 
        dcmRP = True
    elif dcmtype == 'RD': 
        dcmRD = True
    elif dcmtype == 'ALL':
        dcmCT = True
        dcmRS = True
        dcmRP = True
        dcmRD = True
    else:
        print('Wrong output DICOM type provided!')
        exit()

    print('Start creating DICOM Files ...')
    pfDicom = PFDicom(ptdir, dcmdir)
    
    if dcmCT:
        for imgset in pfDicom.Patient.ImageSetList.ImageSet:
            print('Creating DICOM CT for ImageSet_%s ...' % imgset.ImageSetID) 
            pfDicom.createDicomCT(imgset.ImageSetID)
            print('Done!\n')

    if dcmRS:        
        for plan in pfDicom.Patient.PlanList.Plan:
            print('Creating DICOM RS for Plan_%s ...' % plan.PlanID)
            pfDicom.createDicomRS(plan.PlanID)
            print('Done!\n')

    if dcmRD:
        for plan in pfDicom.Patient.PlanList.Plan:
            print('Creating DICOM RD for Plan_%s ...' % plan.PlanID)
            pfDicom.createDicomRD(plan.PlanID)
            print('Done!\n')

    if dcmRP:
        for plan in pfDicom.Patient.PlanList.Plan:
            print('Creating DICOM RP for Plan_%s ...' % plan.PlanID)
            pfDicom.createDicomRP(plan.PlanID)
            print('Done!\n')
