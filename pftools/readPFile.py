'''
readPFile

The structure of the Object coreated will be dynamic based on the file readin.

To use some data, a few checks must be performed first. 
The group of data are list below:

1. CPManagerObject --- plan.Trial as the input

CPManagerObject under CPManager does not always exist. This code processed it by making all under CPManager 
copied to CPManagerObject[0]. Ideally, no special handling is required.

2. ContourList --- plan.Trial as the input

ContourList under BeamModifier does not always exist. Check if Contourlist is None should it be used.

'''

import os
import sys
import logging
import re
import json
import yaml
from yaml.loader import FullLoader
from copy import deepcopy

class obj(object):
    def __init__(self, dict_):
        self.__dict__.update(dict_)

def dict2obj(d):
    return json.loads(json.dumps(d), object_hook=obj)

def readPFile(filename, ptype):
    text = open(filename, 'r', encoding='latin1')
    strlist = ['% A string will never appear. %']
    if ptype == 'plan.Points':
        strlist = ['Poi ={']
    elif ptype == 'plan.roi':
        strlist = ['roi={', 'curve={', 'points={']
    elif ptype == 'Patient':
        strlist = ['ImageSet ={', 'Plan ={']
    elif ptype == 'ImageSet.ImageInfo':
        strlist = ['ImageInfo ={']
    elif ptype == 'plan.Trial':
        strlist = ['Prescription ={', 'Beam ={', 'CPManagerObject ={', 
                    'FilmImage ={', 'BeamModifier ={', 'CurvePainter ={']
    ystr = ''

    logging.info('reading in %s with type %s done.' % (filename, ptype))

    ################################################
    ## remove comments and apply correct indent
    newtext = []
    level = 0
    indent = ''    
    for line in text:
        # remove comment
        if '//' in line:
            line = line.split('//',2)[0]+'\n'
        if '/*' in line:
            line = line.split('/*',2)[0]+'\n'
        if 'date' in line:
            line = line.replace('-', '')
        if ' .' in line:  # in Trial
            line = line.replace(' .', '')
        if 'Points[] ={' in line: # in Trial
            line = line.replace('[]', '')
        if '#' in line:  # in Trial
            line = line.replace('#', '_')
        if len(line.strip())==0:   # remove blank lines
            continue

        # indent the line
        indent = '    ' * level
        line = indent + line.strip() + '\n'
        level = level+1 if '{' in line else level
        level = level-1 if '}' in line else level
        newtext.append(line)
    #for line in newtext:
    #    print(line[:-1])
    text.close()
    logging.info('comments removed and indent corrected')
    ################################################
    
    ################################################
    ## add '-' for lists    
    occured = [False]*len(strlist)
    indentlevel = [0]*len(strlist)
    inloop  = [True]*len(strlist)
    mylevel = 0
    i = -1
    text = []
    preline = ''
    for line in newtext:
        mylevel = int((len(line) - len(line.lstrip())) / 4)
        for ii in range(len(strlist)):
            if mylevel < indentlevel[ii]:
                inloop[ii] = False
                occured[ii] = False
            if strlist[ii] in line:
                i = ii

        if i >= 0 and strlist[i] in line:
            if occured[i]:
                line = '    '*mylevel + '  - \n'
            else:
                line = line + '    '*mylevel + '  - \n'
                indentlevel[i] = mylevel
                inloop[i] = True
                occured[i] = True

        if ptype == 'plan.Trial' and 'ControlPointList ={' in preline and '_0 ={' in line:
            line = '    '*mylevel + 'ControlPoint :\n' + '    '*mylevel + '  - \n'
        if ptype == 'plan.Trial' and 'RowLabelList ={' in preline and '_0 ={' in line:
            line = '    '*mylevel + 'RowLabel :\n' + '    '*mylevel + '  - \n'
        if ptype == 'plan.Trial' and 'LabelFormatList ={' in preline and '_0 ={' in line:
            line = '    '*mylevel + 'LabelFormat :\n' + '    '*mylevel + '  - \n'
        if ptype == 'plan.Trial' and re.search(r'^_[0-9]{1,3}\s={$',line.strip()) is not None:
            line = '    '*mylevel + '  - \n'
        preline = line

        text.append(line)

    #for line in text:
    #    print(line[:-1])
    ################################################

    ################################################
    ## remove unnecessary components
    for line in text:
        line = line.replace('=', ':')
        line = line.replace('{', '')
        line = line.replace('}', '')
        line = line.replace(';', '')
        if len(line.strip()) == 0:
            continue                
        ystr += line
    #print(ystr)
    logging.info(filename + ' conversion to yaml compatible format done')
    ################################################
    
    ################################################
    # convert to python dict from yaml
    yobj = yaml.load(ystr, Loader=FullLoader)
    # print(yobj['Trial']['PrescriptionList']['Prescription'][0]['Color'])
    #print(yobj['Trial'])
    logging.info('yaml loaded as dict')

    ################################################
    # Points in plan.rio are not fully done. Convert to list here
    if ptype == 'plan.roi':
        for iroi in range(len(yobj['roi'])):
            for icurve in range(len(yobj['roi'][iroi]['curve'])):
                pts = [float(pt) for pt in yobj['roi'][iroi]['curve'][icurve]['points'][0].split()]
                yobj['roi'][iroi]['curve'][icurve]['points'] = pts
        logging.info('post-processing dict for Points in plan.roi done')
    #print(yobj['roi'][1]['curve'][0]['points'])
    ################################################
    # Points in plan.Trial not fully done yet. Convert to list here
    if ptype == 'plan.Trial':
        # Trial.BeamList.Beam[].CPManager.CPManagerObject[].ControlPointList.ControlPoint[].ModifierList.BeamModifier[].ContourList.CurvePainter.Curve.RawData.Points
        # Trial.BeamList.Beam[].CPManager.CPManagerObject[].ControlPointList.ControlPoint[].MLCLeafPositions.RawData.Points
        beam = yobj['Trial']['BeamList']['Beam']
        nbeams = len(beam)
        for ibeam in range(nbeams):
            if 'CPManagerObject' not in beam[ibeam]['CPManager']:
                cpmObject = beam[ibeam]['CPManager']
                yobj['Trial']['BeamList']['Beam'][ibeam]['CPManager']['CPManagerObject'] = [ deepcopy(cpmObject) ]
            cpmObject = beam[ibeam]['CPManager']['CPManagerObject']
            ncpmObject = len(cpmObject)

            for icpm in range(ncpmObject):
                cpts = cpmObject[icpm]['ControlPointList']['ControlPoint']
                cpts = cpmObject[icpm]['ControlPointList']['ControlPoint']
                ncpts = len(cpts)
                for icpts in range(ncpts):
                    leafpos = [float(pt) for pt in cpts[icpts]['MLCLeafPositions']['RawData']['Points'].split(',')]
                    cpts[icpts]['MLCLeafPositions']['RawData']['Points']=leafpos
                    #yobj['Trial']['BeamList']['Beam'][ibeam]['CPManager']['CPManagerObject'][icpm]['ControlPointList']['ControlPoint'][icpts]['MLCLeafPositions']['RawData']['Points']=leafpos
                    modifier = cpts[icpts]['ModifierList']['BeamModifier']
                    nmodifier = len(modifier)
                    if modifier[0]['ContourList'] is None:
                        continue # electron cases (or some other cases too?)
                    for imodifier in range(nmodifier):
                        curvepainter = modifier[imodifier]['ContourList']['CurvePainter']
                        ncurvepainter = len(curvepainter)
                        for icurve in range(ncurvepainter):
                            pts = [float(pt) for pt in curvepainter[icurve]['Curve']['RawData']['Points'].split(',')]
                            #yobj['Trial']['BeamList']['Beam'][ibeam]['CPManager']['CPManagerObject'][icpm]['ControlPointList']['ControlPoint'][icpts]['ModifierList']['BeamModifier'][imodifier]['ContourList']['CurvePainter']['Curve']['RawData']['Points']=pts
                            curvepainter[icurve]['Curve']['RawData']['Points']=pts
        logging.info('post-processing dict for Points in plan.Trial done')



    ################################################
    # convert to python obj type
    pystruct = dict2obj(yobj)
    logging.info(filename + ' is a Python Object now.\n')
    return pystruct

if __name__ == '__main__':
    prjpath = os.path.dirname(os.path.abspath(__file__))+'/../'

    FORMAT = "[%(asctime)s %(levelname)s - %(funcName)s] %(message)s"
    logging.basicConfig(format=FORMAT, filename=prjpath+'logs/test.log', level=logging.INFO)

    logging.info('Project foler is %s' % os.path.abspath(prjpath))

    # plan.Points
    Points = readPFile(prjpath+'examples/Patient_6204/Plan_0/plan.Points', 'plan.Points')
    print(Points.Poi[1].Color)

    # plan.roi
    ROIs = readPFile(prjpath+'examples/Patient_6204/Plan_0/plan.roi', 'plan.roi')
    print(len(ROIs.roi[0].curve))

    # ImageSet.header
    Header = readPFile(prjpath+'examples/Patient_6204/ImageSet_0.header', 'ImageSet.header')
    print(Header.y_start, ' -- ', Header.dim_units)

    # Patient
    Patient = readPFile(prjpath+'examples/Patient_6204/Patient', 'Patient')
    print(Patient.PlanList.Plan[0].PlanName)

    # ImageSet.ImageInfo
    ImageInfo = readPFile(prjpath+'examples/Patient_6204/ImageSet_0.ImageInfo', 'ImageSet.ImageInfo')
    print(ImageInfo.ImageInfo[0].TablePosition, ImageInfo.ImageInfo[2].SliceNumber)

    # ImageSet.ImageSet
    ImageSet = readPFile(prjpath+'examples/Patient_6204/ImageSet_0.ImageSet', 'ImageSet.ImageSet')
    print(ImageSet.NumberOfImages)

    # plan.PatientSetup
    PatientSetup = readPFile(prjpath+'examples/Patient_6204/Plan_0/plan.PatientSetup', 'plan.PatientSetup')
    print(PatientSetup.Position)

    # plan.Trial
    PlanTrial = readPFile(prjpath+'examples/Patient_6204/Plan_0/plan.Trial', 'plan.Trial')
    print(PlanTrial.Trial.PrescriptionList.Prescription[0].PrescriptionDose)
    print(PlanTrial.Trial.BeamList.Beam[0].CPManager.CPManagerObject[0].ControlPointList.ControlPoint[1].MLCLeafPositions.RawData.Points[30])
    #print(PlanTrial.Trial.BeamList.Beam[0].CPManager.CPManagerObject[0].ControlPointList.ControlPoint[1].MLCLeafPositions.RawData.Points.split(',')[30])
    print(PlanTrial.Trial.BeamList.Beam[0].CPManager.CPManagerObject[0].ControlPointList.ControlPoint[1].MLCLeafPositions.RowLabelList.RowLabel[0].String)
    print(PlanTrial.Trial.BeamList.Beam[0].CPManager.CPManagerObject[0].ControlPointList.ControlPoint[0].ModifierList.BeamModifier[0].ContourList.CurvePainter.Curve.RawData.Points[4])
    
