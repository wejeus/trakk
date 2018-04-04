#!/usr/local/bin/python3
# author: Samuel Wejeus (samuel@isalldigital.com)
import sys
import argparse
import storage
import os
import git
import link
import base
import config
import log


# if all is good - all is good and don't create anything new otherwise create new repo
def init(path):
    try:
        ref_store = storage.Storage()
        repo = git.Repo(ref_store.get_repository())
        log.info("Repository already exists at location: " + ref_store.get_repository())
        sys.exit(0)
    except Exception as e:
        try:
            storage.Storage.new(path)
            ref_store = storage.Storage() # read back to as a test if all is OK
            assert git.Repo.init(os.path.abspath(path)).__class__ is git.Repo
            log.info("Initialized empty {0} repository in {1}".format(config.APP, ref_store.get_repository()))
        except BaseException as e:
            print(e)
            sys.exit(1)


def clone(params):
    # cloned_repo = repo.clone(join(rw_dir, 'to/this/path'))
    # assert cloned_repo.__class__ is Repo     # clone an existing repository
    if (len(params) != 2):
        log.error("error")
    # TODO: parse and verify first param is path and second is URL
    path = params[0]
    repo_url = params[1]
    try:
        storage.Storage.new(path, create_index=False)
        # store = storage.Storage()
        # repo = git.Repo(store.get_repository())
        git.Repo.clone_from(repo_url, path)
    except BaseException as e:
        log.error(e)
        sys.exit(1)
    sys.exit(1)


def dispatch(command, params):
    if command in base.AVAILABLE_ACTIONS:
        try:
            ref_store = storage.Storage()
            repo = git.Repo(ref_store.get_repository())
            assert not repo.bare

            trakk = base.Base(
                ref_store,
                link.Linker(ref_store.get_repository()),
                repo)

            method = getattr(trakk, command)
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

args = vars(parser.parse_args())

for command in args:
    if args[command]:
        dispatch(command, args[command])

