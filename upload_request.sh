#!/bin/bash

ncftp -u anonymous -p $PASSWD 'ccycle.gps.caltech.edu' << EOF

cd upload
put input_file.txt

bye
EOF
