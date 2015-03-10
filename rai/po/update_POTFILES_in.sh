#!/bin/bash
cd ..;
find . | grep php | grep -v jpgraph | grep -v example > po/POTFILES.in;
cd po;
