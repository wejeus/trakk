
TRAKK
============
- Selective tracking and backup system

# What

Backup utility that lets you keep a mirror of important files that are always in sync with original. The mirror folder lives under version control using git so you can track changes and easy resotre previous versions. The trakk commandline utility helps you in this process with simple commands such as --restore <pathspec>. Trakk is very usefull for keeping various configuration files in sync between several computers (such as if you have one private and one office workstation). Or restoring an overwritten configfile as a result of a software upgrade. Both is easy since the underlying storage mechanism is handled by git and hence it is super simple to push/pull from a central repository.

* Assumption: base dir is always: ~/ and you can only track files relative to your home dir

# Install

* brew install python3
* pip3 install --user pipenv
* pip3 install --user pytest gitpython injector rope

This will install python3 and pip3 in **/usr/local/bin** - make sure to update your PATH to include those. I have experienced issues with pip3 not being installed correctly sometimes, try to clean and chmod **/usr/local** with right permissions: 
	
	sudo chown -R $(whoami) $(brew --prefix)/* 

and then reinstall with 
	
	brew reinstall python3 

# How

Adding a file to trakk results in the following:
* resolves to path relative home dir (~/[file])
* creates hard link to given pathspec: <configured_repo>/[file]
* add entry to ~/.trakk.config list of tracked files

Removing a file from trakk results in the following:
* remove [file] from being tracked (does not remove from git history):
* remove entry from list in ~/.track.config
* remove hard link from repository dir

It's recommended to add trakk run as part of shell startup. That way you will get a quick overview in a timely manner using status check.

$> trakk --status

Usage
--------

Create and init new repo at location <path>. If you later decide to move your <repository> location you can just do new **init** on that location
```
trakk --init <path>
```

### trakk --list
Print list of tracked files

### trakk --status
Show any inconsistencies between original system files and mirror files and folders

### trakk --sync
Synchronize potentially broken links and/or missing files or files detected in track dir but is added as watched files (missing in config). Automatically solves several merges issues.

### trakk --add
Stage files to be included in tracking

### trakk --remove
Remove file from being tracked

# For Development

Setup and run tests in virtual environment:

* pip3 install --user pytest
* (to activate env) $> source virtualenv/bin/activate
* (run a test) $> pytest -o log_cli=true app_test.py (or dont specify a specific file to run all tests)