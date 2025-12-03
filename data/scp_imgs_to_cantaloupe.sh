#!/bin/bash
for filename in ./imgs/*.jpg; do
        echo "Copying $filename to Cantaloupe (deptfod server)"
        scp $filename rigauxp@deptfod.cnam.fr:~rigauxp/cantaloupe/imgs
done
for filename in ./imgs/*.png; do
        echo "Copying $filename to Cantaloupe (deptfod server)"
        scp $filename rigauxp@deptfod.cnam.fr:~rigauxp/cantaloupe/imgs
done