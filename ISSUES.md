# Issues or anything in doubt in implementing P3TK

* ImagePositionPatient:

	- x: should be ImageSet.header.x_start, but to be further verified.
         
          For now, x shifts an extra pixel to match RS and RD positioning set before. To be corrected.

	- y: what is the relationship to y_start and couch_height??

	- z: should be OK.
