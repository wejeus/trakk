#!/usr/local/bin/python3
# author: Samuel Wejeus (samuel@isalldigital.com)
from injector import Module, provider, Injector, inject, singleton

import sys
import argparse
import os
import git
from distutils.util import strtobool

from app_module import AppModule
from linker import Linker
from ref_store import RefStore
from app import App, AVAILABLE_ACTIONS
from config import Config, APP, VERSION
import log

injector = Injector(AppModule())


#_ERROR_REPOSITORY_NOT_EMPTY = "Specified repository path is not empty and/or already exists"
#_ERROR_INITIALAZION_ABORTED = "Initialization aborted"
_ERROR_INVALID_REPOSITORY_PATH_NOT_IN_HOME = "Invalid repository! Repository path must be a subfolder of users home directory"

def check_initialized():
	# test if config exists and repo is valid
	ref_store = injector.get(RefStore)
	ref_store.check_valid()

def setup_repo_and_ref_store(path) -> bool:
	log.debug("trying to setup new ref store and repository..")
	repo_abs_path = os.path.abspath(path)

	if not repo_abs_path.startswith(os.path.expanduser("~")):
		raise IOError(_ERROR_INVALID_REPOSITORY_PATH_NOT_IN_HOME)

	# TODO test what happens if I give non existing path here...
	if not _is_repo_dir_empty(repo_abs_path):
		log.info("Potential repository already exist at location (i.e it is not empty).\nUse as {0} repository? [y/n]".format(APP))
		yes = strtobool(input().lower()) # yes=1, no=0
		if not yes:
			log.info("Aborting..")
			return False

	if not os.path.exists(repo_abs_path):
		log.debug("creating missing directories..")
		os.makedirs(repo_abs_path)

	config = injector.get(Config)
	config.write_rc(repo_abs_path, [])
	ref_store = injector.get(RefStore)
	ref_store.reload()
	return True

def _is_repo_dir_empty(abspath):
    for _, _, files in os.walk(abspath):
        if files:
            return False
    return True

# test to see if already exists otherwise create new
def init(path):
	ref_store = injector.get(RefStore)

	try:
		check_initialized()
		log.info("Repository already exists at location: " + ref_store.get_repository())
		sys.exit(0)
	except Exception:
		pass

	try:
		if setup_repo_and_ref_store(path):
			assert git.Repo.init(os.path.abspath(path)).__class__ is git.Repo
			log.info("Initialized {0} repository in {1}".format(APP, ref_store.get_repository()))	
	except BaseException as e:
		print(e)
		sys.exit(1)

# TODO: build and verify
def clone(params):
	# cloned_repo = repo.clone(join(rw_dir, 'to/this/path'))
	# assert cloned_repo.__class__ is Repo     # clone an existing repository
	if (len(params) != 2):
		log.error("error")
	# TODO: parse and verify first param is path and second is URL
	path = params[0]
	repo_url = params[1]
	try:
		# TODO must create new index with refs from repo
		# TODO need to --sync afterwards, figure out how to solve --sync here..
		# repo = git.Repo(store.get_repository())
		git.Repo.clone_from(repo_url, path)
	except BaseException as e:
		log.error(e)
		sys.exit(1)
	sys.exit(1)

def dispatch(command, params):
	if command in AVAILABLE_ACTIONS:
		try:
			check_initialized()
			trakkApp = injector.get(App)
			method = getattr(trakkApp, command)
			method(params)
		except BaseException as e:
			log.error(e)
			sys.exit(1)
	else:
		if command == 'init':
			init(params)
		if command == 'clone':
			clone(params)


parser = argparse.ArgumentParser(description='Backup and tracking of files using inode linking (hard links) and version control (git)')

parser.add_argument('--version',
					action='version', version="{0} version {1}".format(APP, VERSION))

# Creation (defaults to current directory)
parser.add_argument('--init',
					type=str, action='store',
					help='Create and init new repo at location <path>')

# TODO
# parser.add_argument('--clone',
# 					type=str, action='store', nargs='+',
# 					help='Create new local repository from existing. Needs <path> and a remote <url>')

parser.add_argument('--list',
					action='store_true',
					help='Print list of tracked files')

parser.add_argument('--status',
					action='store_true',
					help='Show any inconsistencies between original system files and mirror files and folders')

parser.add_argument('--sync',
					action='store_true',
					help='Synchronize potentially broken links and/or missing files or files detected in trakk dir but is added as watched files in git (i.e. missing in index)')

# Handling, modifier commands (needs one or more arguments)
# maybe remove dest

parser.add_argument('--add',
					type=str, dest='add', nargs='+', metavar="<pathspec>",
					help='Stage a file or directory to be included in tracking')

parser.add_argument('--remove',
					type=str, dest='remove', nargs='+', metavar="<pathspec>",
					help='Remove file or directory from being tracked')

parser.add_argument('--show',
					type=str, dest='show', nargs='+', metavar="<pathspec>",
					help='Show diff for file')

if len(sys.argv)==1:
	try:
		ref_store = injector.get(RefStore)
		log.info("Trakk is live in: {0}".format(ref_store.get_repository()))
	except IOError as e:
		log.info("{0}\n".format(e))
		parser.print_help()
	sys.exit(1)

args = vars(parser.parse_args())
for command in args:
	if args[command]:
		dispatch(command, args[command])
