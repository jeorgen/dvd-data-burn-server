import time
import os
import shutil
import subprocess
import argparse
import logging
from ConfigParser import SafeConfigParser, NoSectionError
import utils

DEFAULT_CONFIG = "etc/session_server.config"
arg_parser = argparse.ArgumentParser(description='Session server, feeding burn server')
arg_parser.add_argument('-c', default=DEFAULT_CONFIG, help="Config file, see %s.example" % DEFAULT_CONFIG)
args = arg_parser.parse_args()

parser = SafeConfigParser()
parser.read(args.c)

try:
    SRC_DIR = parser.get('LOCATIONS', 'SRC_DIR')
    SESSION_BASE_PARENT_DIR = parser.get('LOCATIONS', 'SESSION_BASE_PARENT_DIR')
    MINUTES_BETWEEN_SESSIONS = int(parser.get('SESSION FREQUENCY', 'MINUTES_BETWEEN_SESSIONS'))
    POLLING_INTERVAL_IN_SECS = int(parser.get('ADVANCED', 'POLLING_INTERVAL_IN_SECS'))
    FIND_COMMAND_LOCATION = parser.get('ADVANCED', 'FIND_COMMAND_LOCATION')
    FILE_COUNT_FOR_IMMEDIATE_SESSION = int(parser.get('SESSION FREQUENCY', 'FILE_COUNT_FOR_IMMEDIATE_SESSION'))
except NoSectionError as e:
    utils.missing_or_bad_config(e, attempted_file = args.c, example_file = "%s.example" % DEFAULT_CONFIG)

last_session_time = 0

FIND_ALL_COMMAND = "Defined below"
FIND_NEW_COMMAND = "Defined below"  

def reconfigure_commands():
    """ This function useful for testing"""
    global FIND_ALL_COMMAND, FIND_NEW_COMMAND
    FIND_ALL_COMMAND = [FIND_COMMAND_LOCATION, SRC_DIR, "-type", "f"]
    FIND_NEW_COMMAND = FIND_ALL_COMMAND + ["-cmin",]

reconfigure_commands()

def enough(files):
    return len(files) >= FILE_COUNT_FOR_IMMEDIATE_SESSION

def compute_now_in_minutes():
    return int(time.time()/60) 

def minutes_since_last_session():
    return compute_now_in_minutes() - last_session_time

def time_to_session(minutes_since_last):
    return minutes_since_last >= MINUTES_BETWEEN_SESSIONS    

def add_burn_signal(dir_path):
    file_name = os.path.join(dir_path, 'burn_signal')
    make_file_path(file_name)
    fo = open(file_name, 'w')
    fo.write('burn')
    fo.close()

def get_new_files(command):
    pipes = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    new_files, std_err = pipes.communicate()
    if std_err:
        raise OSError(std_err)
    if not new_files:
        return []
    return [new_file for new_file in new_files.split('\n') if new_file]

def make_file_path(dst):
    if not os.path.exists(os.path.dirname(dst)):
        logging.info( "path '%s' does not exist for dst '%s', let's make one" % (os.path.dirname(dst), dst))
        try:
            os.makedirs(os.path.dirname(dst))
        except OSError as exc:
            if exc.errno != errno.EEXIST:
                raise
    return dst

def copy_file(src, dst):
    make_file_path(dst)
    shutil.copy(src, dst)

def dst(file_path, dst_base_dir):
    rel_path = os.path.relpath(file_path, SRC_DIR)
    return os.path.join(dst_base_dir, rel_path)

def copy_files(files, dst_base_dir):
    for file_path in files:
        copy_file(file_path, dst(file_path, dst_base_dir))

def new_signal_dir():
    return os.path.join(SESSION_BASE_PARENT_DIR, str(time.time()))    

def session(files):
    global last_session_time
    if not files:
        return
    signal_dir = new_signal_dir()
    dst_base_dir = os.path.join(signal_dir, 'files')
    copy_files(files, dst_base_dir)
    add_burn_signal(signal_dir)
    last_session_time = compute_now_in_minutes()
    return signal_dir


def do_job():
    if last_session_time == 0:
        files_to_session = get_new_files(FIND_ALL_COMMAND)
    else:
        minutes_since_last = minutes_since_last_session()
        files_to_session = get_new_files(FIND_NEW_COMMAND + [str(minutes_since_last +1)]) # +1 min. extra for safety
        if not enough(files_to_session) and not time_to_session(minutes_since_last):
            files_to_session = None
    session(files_to_session)

def main():
    while True:
        do_job()
        time.sleep(POLLING_INTERVAL_IN_SECS)


if __name__ == '__main__':
    main()
