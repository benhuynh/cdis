#!/bin/bash
#Author: Ben Huynh
#This script subsets a series of hyperion band images based on geographic coordinates, creating a new folder of subsetted band images.
#Usage: ./subset.sh sceneid newfoldername xoff yoff xsize ysize
FOLDER=/glusterfs/users/bhuynh/cavsarps/$1
cd $FOLDER
mkdir $2
cp *_MTL_L1T.TXT $2
for f in *.TIF
do 
    id=$(basename $f _L1T.TIF)
    echo "Subsetting image for: $id"
    output=${FOLDER}/$2/${id}_${2}_L1T.TIF
    echo "Output: $output"
    gdal_translate -projwin $3 $4 $5 $6 $f $output
done