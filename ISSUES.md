# Issues or anything in doubt in implementing P3TK

* ImagePositionPatient:

	- x: should be ImageSet.header.x_start, but to be further verified.
         
          For now, x shifts an extra pixel to match RS and RD positioning set before. To be corrected.

          Should it be -10.0*x_start? Or 10.0*x_start? To be further tested.

	- y: what is the relationship to y_start and couch_height??

	- z: should be OK.
