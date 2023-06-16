#!/bin/bash
FILES=~/git/Saint-Saens/Transcriptions/*
EXTENSIONS=("sib" "xml" "mei"  "json")
CIBLE=../data/composers-datasets/saintsaens/
for dir in $FILES
do
  if [ -d $dir ];
  then
    for f in $dir/*
    do
      ext="${f##*.}"

      for extension in ${EXTENSIONS[@]}; do
       if [[ $ext == $extension ]]; then
           echo "Found Sibelius file in $dir: $f"
           cp $f $CIBLE
       fi
     done
    done
  fi
done
