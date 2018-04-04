
TRAKK
============
- Simple tracking and backup system

# What

Backup utility that lets you keep a mirror of important files that are always in sync with original. The mirror folder lives under version control using git so you can track changes and easy resotre previous versions. The trakk commandline utility helps you in this process with simple commands such as --restore <pathspec>. Trakk is very usefull for keeping various configuration files in sync between several computers (such as if you have one private and one office workstation). Or restoring an overwritten configfile as a result of a software upgrade. Both is easy since the underlying storage mechanism is handled by git and hence it is super simple to push/pull from a central repository.

* Assumption: base dir is always: ~/
* If new tracked entry masks previous entry remove previous and use more general entry

# Install
* brew install python3 # this will install python3 and pip3 in /usr/local/bin - make sure to update your PATH to include those. I have experienced issued with pip3 not being installed, try to clean chmod /usr/local to right permission "sudo chown -R $(whoami) $(brew --prefix)/*" and reinstall with $> brew reinstall python3 
* pip3 install --user pipenv
* pip3 install --user gitpython (old way: Needs GitPython: sudo easy_install gitpython)

# How

Adding a file to trakk results in the following:
* resolves to path relative home dir (~/[file])
* creates hard link to given pathspec: <configured_repo>/[file]
* add entry to ~/.trakk.config list of tracked files

Removing a file from trakk results in the following:
* remove [file] from being tracked (does not remove from git history):
* remove entry from list in ~/.track.config
* remove hard link from repository dir

Usage
--------


Create and init new repo at location <path>
```
trakk --init <path>
```




### trakk --list
Print list of tracked files

### trakk --status
Show any inconsistencies between original system files and mirror files and folders

### trakk --sync
Synchronize potentially broken links and/or missing files or files detected in track dir but is added as watched filed (missing in config)

### trakk --add
Stage pathspec(s) to be included in tracking

### trakk --remove
Remove pathspec(s) from being tracked

References
--------
* http://docs.python-guide.org/en/latest/dev/virtualenvs/