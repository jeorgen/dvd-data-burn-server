import os
import time
import shutil
import subprocess
import argparse
from ConfigParser import SafeConfigParser, NoSectionError
import utils

DEFAULT_CONFIG = "etc/burn_server.config"
arg_parser = argparse.ArgumentParser(description='Burn server, burning sessions to disk')
arg_parser.add_argument('-c', default=DEFAULT_CONFIG, help="Config file, see %s.example" % DEFAULT_CONFIG)
args = arg_parser.parse_args()

parser = SafeConfigParser()
parser.read(args.c)

try:
    WATCHED_FOLDER = parser.get('DIRECTORIES', 'WATCHED_FOLDER')
    BURNER_LOCATION = parser.get('BURNER', 'BURNER_LOCATION')
    XORRISO_LOCATION = parser.get('BURNER', 'XORRISO_LOCATION')
except NoSectionError as e:
    utils.missing_or_bad_config(e, attempted_file = args.c, example_file = "%s.example" % DEFAULT_CONFIG)

BURN_COMMAND = [XORRISO_LOCATION, '-dev', BURNER_LOCATION, '-add']
INFO_COMMAND = [XORRISO_LOCATION, '-indev', BURNER_LOCATION ,'-du', '--']
# MEDIA_SUMMARY_PATTERN = re.compile(r'^Media summary: (\d+) sessions*, (\d+) data blocks, ([\d.]+) data, ([\d.]+). free')

def get_top_level_files(path):
    files=[os.path.join(path, thing) for thing in os.listdir(path) if os.path.isfile(os.path.join(path, thing))]
    return files

def get_directories(path):
    res = [os.path.join(path, directory) for directory in os.listdir(path) if os.path.isdir(os.path.join(path, directory))]
    return res

def dir_ready(path):
    """ Checks if the dir is ready for burning. i.e it has
        a file at the top level""" 
    files = get_top_level_files(path)
    return len(files) > 0

def get_burn_candidates():
    candidates =  [directory for directory in get_directories(WATCHED_FOLDER) if dir_ready(directory)]
    return candidates

def burn(subdir, testing = False):
    print "burning with" 
    command = BURN_COMMAND + [subdir]
    if testing:
        return command
    status = subprocess.check_call(command)
    print "burned"
    # TODO: Check if it fails, why. If disk is full, then operator
    # notification is needed, if no rights then a sudo umount may be needed

# def get_drive_info():
#     pipes = subprocess.Popen(INFO_COMMAND, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
#     std_out, std_err = pipes.communicate()
#     return std_err

# def get_disk_info(info):
#     for line in info.split('\n'):
#         if line.startswith('Media summary'):
#             _, data = line.split(':')
#             items = data.split(',')

#             # Media summary: 7 sessions, 17424 data blocks, 34.0m data, 4421m free


def get_sub_directory(path):
    """ Returns first sub directory it encounters. There should be only one """
    subdirs = [os.path.join(path,directory) for directory in os.listdir(path) if os.path.isdir(os.path.join(path,directory))]
    adir = os.path.join(path,subdirs[0]) # We want this to throw an exception
    return adir

def mark_as_burned(path):
    # remove all top level files
    for afile in  get_top_level_files(path):
        os.unlink(os.path.join(path, afile))
    # name the dir as burned
    shutil.move(path, path + '-burned')

if __name__ == '__main__':
    while True: #Watch loop
        print "looping"
        for candidate in get_burn_candidates():
            burn(get_sub_directory(candidate))
            mark_as_burned(candidate)
        time.sleep(5)


