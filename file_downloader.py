# Script to download podcast audio files 

import glob
from typing import Union
from pathlib import Path
import os
import wget
from datetime import datetime
from urllib.request import urlopen
import pandas as pd


# Set the source data directory
DATA_DIRECTORY = './data/clean/*.xlsx'

# Get the most recent data file from the directory
files = sorted(glob.iglob(DATA_DIRECTORY),
               key=os.path.getctime,
               reverse = True)
latest = files[0]

# Read in the data file
data = pd.read_excel(latest)

# Define custom function to check whether file already downloaded
def file_exists_in_directories(
        directory_path: Union[str, Path],
        filename: str,
) -> bool:
    """Indicates with True or False whether a filename or filename pattern
    exists in the specified directory *or* in any subdirectory of that
    directory."""
    return len([file for file in Path(directory_path).rglob(filename)
                if file.is_file()]) > 0

# Define custom function to download files and save logfile with results
def download_files(urls, target_directory):

    """Downloads files from url list to specified directory."""

    ls_tmp = []
    successes = 0
    skips = 0
    failures = 0
    id = 1
    file_name = int()
    now = datetime.now()
    datetime_string = now.strftime("%Y%m%d_%H%M%S")
    dir_path = target_directory+datetime_string
    os.mkdir(dir_path)

    for url in urls:

        try:
            response = urlopen(url)
            file_name = wget.detect_filename(response.url)
            file_name_id = str(id)+"_"+str(file_name)
            file_exists = file_exists_in_directories(
                target_directory, file_name_id)
            if file_exists:
                ls_tmp.append(str(id)+" "+str(url)+
                              " skipped (file already exists)")
                print(str(id)+" "+str(file_name)+
                      " skipped (file already exists)")
                skips = skips + 1
            else:
                file_path = dir_path+"/"+file_name_id
                wget.download(url, file_path)
                ls_tmp.append(str(id)+" "+str(url)+
                              " successfully saved as "+str(file_name))
                print(str(id)+" "+str(file_name)+
                      " successfully saved")
                successes = successes + 1

        except:
            ls_tmp.append(str(id)+" "+str(url)+" failed to download")
            print(str(id)+" Failed to download")
            failures = failures + 1

        id = id+1

    print("Succeeded: "+str(successes)+"/"+str(len(urls)))
    print("Skipped: "+str(skips)+"/"+str(len(urls)))
    print("Failed: "+str(failures)+"/"+str(len(urls)))
    ls_tmp.append("Succeeded: "+str(successes)+"/"+str(len(urls)))
    ls_tmp.append("Skipped: "+str(skips)+"/"+str(len(urls)))
    ls_tmp.append("Failed: "+str(failures)+"/"+str(len(urls)))

    output_file = open(dir_path+"/"+'logfile.txt', 'w')

    for item in ls_tmp:
        output_file.write(item + '\n')

    output_file.close()


# Define source urls and target directory 
urls = data["url"]
target_directory = './audio/'

# Apply the function
download_files(urls=urls, target_directory=target_directory)