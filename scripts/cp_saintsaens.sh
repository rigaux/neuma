#!/bin/bash
FILES=~/git/Saint-Saens/Transcriptions/*
EXTENSIONS=("sib" "xml" "mei"  "json")
CIBLE=../data/composers-datasets/saintsaens/

EXTENSIONS=("musicxml")
CIBLE=/Users/philippe/Documents/workspace/dataset/ground_truth
for dir in $FILES
do
  if [ -d $dir ];
  then
    for f in $dir/*
    do
      ext="${f##*.}"

      for extension in ${EXTENSIONS[@]}; do
       if [[ $ext == $extension ]]; then
           echo "Found  file in $dir: $f"
           cp $f $CIBLE
       fi
     done
    done
  fi
done
