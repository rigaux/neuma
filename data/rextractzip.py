from zipfile import ZipFile
import sys
import os
import shutil
import argparse

def unpack_zip(zipfile, path_from_local='.'):
    filepath = os.path.join (path_from_local,zipfile)
    extract_path = os.path.splitext(filepath)[0]
    print ("File path = " + filepath + " Extract path " + extract_path)
    parent_archive = ZipFile(filepath)
    parent_archive.extractall(extract_path)
    namelist = parent_archive.namelist()
    parent_archive.close()
    for name in namelist:
        try:
            if name[-4:] == '.zip':
                unpack_zip(zipfile=name, path_from_local=extract_path)
                os.remove(os.path.join(extract_path, name))
        except:
            print ('failed on' + name)
            pass
    return extract_path

    # you can just call this with filename set to the relative path and file.
    path = unpack_zip(filename)

def main(argv):
    #zip_file = read_cmd_line(argv)
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input", help="Input file name")
    args = parser.parse_args()
    if not args.input:
        print("Please provide a zip file name")
        exit()
    # Unzip the main file first
    unpack_zip(args.input, ".")

if __name__ == "__main__":
    main(sys.argv)
