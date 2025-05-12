# p3tk

Pinnacle3 Toolkit for Pinnacle backup file processing

Pinnacle3 backup files cannot be imported directly by other treatment planning systems (TPS), such as Eclipse. 
This toolkit will generate DICOM files from Pinnacle backups which can be readily imported by other TPS.

To setup the running environment for the first run, you need to go to the project directory and run commands below:

```
python3 -m venv venv
. rc.pyenv
pip install -upgrade pip
pip install -r requirements.txt
```

Later on, to bring the development/running environment back, simply run:

```
. rc.pyenv
```

To create DICOM files from your Pinnacle backup, run command below:

```
python3 app.py -i backup_patient_folder
```

or

```
python3 app.py -i backup_patient_folder -o dicom_output_folder -t ALL
```

The `-t` switch specifies the output DICOM files be CT, RS, RP, RD, or ALL.


=========================================================================

Some backgroud:

We had Pinnacle3 system as the TPS in our center. In 2011, we fully moved away 
to Eclipse for better system integration with ARIA. 
Old treatment plans were still kept in Pinnacle. Whenever a Pinnacle plan 
was required for review, we would export the plan to Eclipse and do a re-calc. 
In 2020, the Pinnacle system, with no vendor support for years, was finally down. 
We still receive requests of retrieving Pinnacle plans, which 
has brought us a huge challenge. We have the options of bringing the vendor back 
to rebuild the whole Pinnacle system, or re-creating plans based 
on information in the Pinnacle backup files, which are fortunately in text format.

While I was seeking for the possibility of recovering Pinnacle plans from the backup
files, I noticed a program Pinnacle-tar-DICOM 
(https://github.com/AndrewWAlexander/Pinnacle-tar-DICOM) by Andrew Alexander. 
While I ran the program for our plans, 
I could only create the correct DICOM CT. There was a coordinate transformation issue
with DICOM RTSTRUCT. There were also problems in importing the generated 
DICOM RTPLAN and RTDOSE to Eclipse. 
I tried to modify the program for fixing the issues 
but it turned out to be hard to follow and understand the code. Even though,
it conceptually demonstrated that it is possible to interprete the Pinnacle backups
and create DICOM files that can be imported to other systems, such as Eclipse.
That was how this piece of code started. 

Thanks Andrew for sharing his Pinnacle-tar-DICOM which makes this small project
possible. I learned a lot from his code, in both Pinnacle backup file interpreting 
and DICOM generating. 

This toolkit, p3tk, will be available on github for anyone interested, 
especially for those facing the similar situation as us when moving away 
from Pinnacle, as an alternative option to Andrew's Pinnacle-tar-DICOM.

I would be very pleased to hear any recommendations/suggestions to improve p3tk, 
or your experience in using p3tk. There are still many limitations (listed
in each release notes) with this code at this stage, 
especially when we have no Pinnacle system for verifications.
Any feedback will be greatly appreciated. It will help to improve 
the functionality and fix the issues in p3tk.
