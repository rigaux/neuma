#!/bin/sh
for i in 01 02 03 04 05 06 07 08 09 10 11 12 13 14 15 16 17 18 19 20
do
  echo "Get canzone$i"
  curl -o "canzone$i.krn" "https://kern.humdrum.org/cgi-bin/ksdata?location=users/craig/classical/frescobaldi/canzoni&file=canzoni$i.krn&format=kern"
done
for i in 21 22 23 24 25 26 27 28 29 30 31 32 33 34 35 36 37 38 39 40
do
  echo "Get canzone$i"
  curl -o "canzone$i.krn" "https://kern.humdrum.org/cgi-bin/ksdata?location=users/craig/classical/frescobaldi/canzoni&file=canzoni$i.krn&format=kern"
done
