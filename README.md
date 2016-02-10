# DVD-data-burn-server

This is alpha software.

The purpose of DVD-data-burn-server is to burn data to a DVD disk, just by a simple transfer of a directory tree (with scp, rsync, ftp, sftp or anything else that can move files) to the server. DVD-data-burn-server will _wait_ to burn the tree until the transfer is complete, waiting for a special file to say it's time to burn. More transfers of directory trees can be done, burning new sessions to the disk, until the disk is full. 

Synopsis

    python burn_server.py 

or

    python burn_server.py -c <config_file>

[The config file](./etc/burn_server.config.example) should by default be in ```etc/burn_server.config```. Use ```etc/burn_server.config.example``` as a template.

## Dependencies
You need the xorriso DVD-burning program installed. On Ubuntu Linux that is:

    apt-get install xorriso

Tested on Ubuntu 15.04 and Ubuntu 15.10 with Xorriso 1.3.2 with a Samsung SE-208GB external portable USB DVD burner drive.

## Use cases

* Any data you want to commit to a read-only media while the data is fresh

* Logs to be burned soon after the events are happening

* New photos or other newly created stuff (e-mails, text messages, documents) that you want to have a read-only copy of if hard disks or cloud storage get inaccessible or involuntarily encrypted


## How it works

Directories and files below can have any names you like

* There is a _watched directory_ that DVD-data-burn-server watches, for sessions to burn. Set the path to it in [the config file](./etc/burn_server.config.example)

* Inside of the _watched directory_ you put session directories

* Inside each session directory you make a data directory, where you put the file tree you want to burn in a session

* Finally, when it is time to burn the session, you leave a _time to burn_ file in the session directory, one step above your data. This file can have any name and contain anything

* DVD-burn-server detects the _time to burn_ file and burns the data directory to disc in a session

If you are using DVD+R, you can burn 153 sessions before it's time to switch in a new disk. For DVD-R it is 99 sessions.

After burning, the server removes the _time to burn_  file and the session directory gets "-burned" appended to its name

An example, burning the files of ```my_files_dir``` via rsync:

## Example

Move my_files_dir over to the server and nest it inside an empty dir, e.g. ```myfiles-session-dir```:

    rsync -r my_files_dir server:/path/to/watched_dir/myfiles-session-dir/

Wait for the files to be transferred over to ```/path/to/watched_dir/myfiles-session-dir/my_files```.
When ready, put some kind of file inside the ```/path/to/watched_dir/myfiles-session-dir```
to trigger the burning (Here we are transferring the file ```/etc/issue``` which is always available on Fedora, CentOS, RHEL, Debian and Ubuntu systems):

    scp /etc/issue server:/path/to/watched_dir/myfiles-session-dir/

That file will trigger the burning!

So in essence, data should be wrapped two levels deep, like this:

    -watched_dir (already on the server)
        -session_dir (created by you)
            -dir_to_be burned (sub directory with your data)
               files.txt
               -dir1
               -dir2
                ...and so on

With the _time to burn_ file it looks like this and is ready for burning:

    -watched_dir (already on the server)
        -session_dir (created by you)
            a_file.txt (signals ready for burning)
            -dir_to_be burned (sub directory)
               files.txt
               -dir1
               -dir2
                ...and so on

## Error handling

No much. If the server stops, it may be because the disc is full. Then it is time for manual intervention, put a new disc in the DVD-burner and restart the server.


## Running it as a service

I use supervisor for this. This is an example configuration file for supervisor, to be put in /etc/supervisor/config.d/ or equivalent:

    [program:dvd_data_burn_server]
    command = /path/to/python /path/to/burn_server/burn_server.py
    process_name=%(program_name)s
    numprocs=1
    directory=/path/to/burn_server
    stopsignal=TERM
    user=auser

## Config

Look at [the example config](./etc/burn_server.config.example)

## session_server.py

session_server.py is not needed to use burn_server.py, but can be useful. session_server.py watches a directory and every n minutes it checks if there are any new files, in which case it transfers _only those_ files to a new session directory in the watched directory of burn_server.py, and signals it to burn them to disc. The idea is to skim off any new files appearing in a backup and burn only those. 

Check [etc/session_server.config.example](./etc/session_server.config.example) for configuration settings. If you would be using rsync to update your backup, use the -u or -c switch so that only newly transferred files are timestamped as new. See http://jorgenmodin.net/index_html/rsync-and-the-resulting-time-stamps

Config file should by default be in ```etc/session_server.config```.

It may be possible to do something similar with xorriso directly, but the man page for xorriso 1.3.2 lists 344 command line switches, and some of them can be combined...

## Running session_server as a service

I use supervisor for this. This is an example configuration file for supervisor, to be put in /etc/supervisor/config.d/ or equivalent:

    [program:dvd_data_burn_server]
    command = /path/to/python /path/to/session_server/session_server.py
    process_name=%(program_name)s
    numprocs=1
    directory=/path/to/session_server
    stopsignal=TERM
    user=auser


## session_server.py config

Look at [the example config](./etc/session_server.config.example)


## Future directions

Some ideas:

* Better error handling

* Check how many sessions and how much space is left before burning (however the server should just terminate on error, and after replacement of the disc and restart of the server, it should commence burning again. Hopefully)

* Having DVD-data-burn-server leave signal files of its own in the watched directory when something goes wrong. E.g. a disk gets full and DVD-data-burn-server can leave a "Disk is full" signal file, which can then be picked up by a notifier that e-mails or texts the admin, or files a ticket that it is time to change disks.

* Supporting several DVD burners so one can move on to the next when one gets full

* You can already use several DVD burners in parallel by having this program run in multiple instances with different config files with different device settings