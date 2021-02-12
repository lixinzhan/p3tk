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

    ptdir = args.input
    if args.output:
        dcmdir = args.output
    else:
        dcmdir = '.'

    dcmCT = False
    dcmRS = False
    dcmRP = False
    dcmRD = False
    if args.type:
        dcmtype = args.type
    else:
        dcmtype = 'ALL'

    if dcmtype == 'CT': dcmCT = True
    elif dcmtype == 'RS': dcmRS = True
    elif dcmtype == 'RP': dcmRP = True
    elif dcmtype == 'RD': dcmRD = True
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
            pfDicom.createDicomCT(imgset.ImageSetID)
            print('DICOM ImageSet_%s created!' % imgset.ImageSetID) 

    if dcmRS:        
        for plan in pfDicom.Patient.PlanList.Plan:
            pfDicom.createDicomRS(plan.PlanID)
            print('DICOM RTStruct_%s created!' % plan.PlanID)

    if dcmRD:
        for plan in pfDicom.Patient.PlanList.Plan:
            pfDicom.createDicomRD(plan.PlanID)
            print('DICOM RD for Plan_%s created!' % plan.PlanID)

    if dcmRP:
        for plan in pfDicom.Patient.PlanList.Plan:
            pfDicom.createDicomRP(plan.PlanID)
            print('DICOM RP for Plan_%s created!' % plan.PlanID)
