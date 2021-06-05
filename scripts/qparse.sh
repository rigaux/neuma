#!/bin/bash
#
# Inputs#
#   - qparse_bin_dir: directory of the QParse program
#   - config_file_path: full path to the param file (include the file name itself)
#   - grammar_file: path to the grammar file
#   - input_file: path to the input file (MIDI)
#   - output_file: path of the file where QParse stores its output
#

echo
echo ==== Run Qparse program

export PATH=$PATH:{qparse_bin_dir}
# /home/scorelibadmin/qparselib/build/

# Clean


# Run QParse with
equiv2 -v 5 -i {input_file} -a {grammar_file} -o {output_file} -config {config_file_path}

