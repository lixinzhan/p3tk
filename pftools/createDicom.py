import os
import sys
import logging
from pftools.readPFile import readPFile

def createDicom():
    pass


if __name__ == '__main__':
    prjpath = os.path.dirname(os.path.abspath(__file__))+'/../'

    FORMAT = "[%(asctime)s %(levelname)s - %(funcName)s] %(message)s"
    logging.basicConfig(format=FORMAT, filename=prjpath+'logs/test.log', level=logging.INFO)

    logging.info('Running createDicom tests ...')
