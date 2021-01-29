# p3tk
Pinnacle3 Toolkit for Pinnacle backup file processing

Pinnacle3 backup files cannot be imported directly by other treatment planning system, such as Eclipse. 
This tool is used for creating the DICOM files from Pinnacle backups.

To setup the running environment for the first time, run at the project directory:

python3 -m venv venv
. rc.pyenv
pip install -upgrade pip
pip install -r requirements.txt

Later on, to bring the development/running environment back, simply run

. rc.pyenv

