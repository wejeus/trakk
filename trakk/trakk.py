#!/usr/local/bin/python3
# author: Samuel Wejeus (samuel@isalldigital.com)
import sys
import argparse
from ref_store import RefStore
import os
import git
import link
from app import App, AVAILABLE_ACTIONS
import config
import log

# test to see if already exists otherwise create new
def init(path):
	try:
		ref_store = RefStore()
		if ref_store.check_valid():
			log.info("Repository already exists at location: " + ref_store.get_repository())
			sys.exit(0)
	except IOError as e:
		try:
			ref_store = RefStore.new(path)
			assert git.Repo.init(os.path.abspath(path)).__class__ is git.Repo
			log.info("Initialized empty {0} repository in {1}".format(config.APP, ref_store.get_repository()))	
		except BaseException as e:
			print(e)
			sys.exit(1)

# TODO: verify and test
def clone(params):
	# cloned_repo = repo.clone(join(rw_dir, 'to/this/path'))
	# assert cloned_repo.__class__ is Repo     # clone an existing repository
	if (len(params) != 2):
		log.error("error")
	# TODO: parse and verify first param is path and second is URL
	path = params[0]
	repo_url = params[1]
	try:
		RefStore.new(path, create_index=False)
		# store = storage.Storage()
		# repo = git.Repo(store.get_repository())
		git.Repo.clone_from(repo_url, path)
	except BaseException as e:
		log.error(e)
		sys.exit(1)
	sys.exit(1)

def dispatch(command, params):
	if command in AVAILABLE_ACTIONS:
		try:
			ref_store = RefStore()
			repo = git.Repo(ref_store.get_repository())
			assert not repo.bare

			trakkApp = App(
				ref_store,
				link.Linker(ref_store.get_repository()),
				repo)

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
					action='version', version="{0} version {1}".format(config.APP, config.VERSION))

# Creation (defaults to current directory)
parser.add_argument('--init',
					type=str, action='store',
					help='Create and init new repo at location <path>')

parser.add_argument('--clone',
					type=str, action='store', nargs='+',
					help='Create new local repository from existing. Needs <path> and a remote <url>')

parser.add_argument('--list',
					action='store_true',
					help='Print list of tracked files')

parser.add_argument('--status',
					action='store_true',
					help='Show any inconsistencies between original system files and mirror files and folders')

parser.add_argument('--sync',
					action='store_true',
					help='Synchronize potentially broken links and/or missing files or files detected in track dir but is added as watched filed (missing in config)')

# Handling, modifier commands (needs one or more arguments)
# maybe remove dest

parser.add_argument('--show',
					type=str, dest='show', nargs='+', metavar="<pathspec>",
					help='Show')

parser.add_argument('--add',
					type=str, dest='add', nargs='+', metavar="<pathspec>",
					help='Stage pathspec(s) to be included in tracking')

parser.add_argument('--remove',
					type=str, dest='remove', nargs='+', metavar="<pathspec>",
					help='Remove pathspec(s) from being tracked')

if len(sys.argv)==1:
	try:
		ref_store = RefStore()
		log.info("Trakk is live in: {0}".format(ref_store.get_repository()))
	except IOError as e:
		log.info("{0}\n".format(e))
		parser.print_help()
	sys.exit(1)

args = vars(parser.parse_args())
for command in args:
	if args[command]:
		dispatch(command, args[command])

