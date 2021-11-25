#!/bin/bash

lftp -u  anonymous,$PASSWD 'ccycle.gps.caltech.edu' << EOF

cd upload
put input_file.txt

bye
EOF
