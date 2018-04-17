# author: Samuel Wejeus (samuel@isalldigital.com)
import os
import json
import config
import log

# a <ref> is pointer to a local file given by its <user_home> relative path.
# Example: "<track dir>/.gitconfig is the ref to the real file ~/.gitconfig
# but normalized relative to track dir. That is is the track dir is omitted and result is just .gitconfig.
# All files are (unless defined explicitly defined in config) assumed to be relative home dir (~/)

# RefStore
#
# Storage consists of, and handles, a <rc> and <index> file located in <user home> and <repo> respectively
# The <rc> holds a pointer to the repo and other potential configs for Trakk in general
# The <index> is and index if traked files and is intended to be part of the version controled files

# <rc> have to look like this: {"repository": "/Users/sawe/git/isalldigital.com/system"} (using absolute paths)

_JSON_KEY_REPOSITORY = 'repository'
_JSON_KEY_REFS = 'refs'

_ERROR_INVALID_REPOSITORY_PATH = "Repository path must exist and be a sub folder to users home directory"
_ERROR_NOT_INITIALIZED = "Trakk not yet initialized!"
_ERROR_NOT_TRACKED = "File not tracked"
_ERROR_ALREADY_TRACKED = "File already tracked"
_ERROR_REPOSITORY_NOT_EMPTY = "Specified repository path is not empty and/or already exists"

# returns valid (repository) or empty
def read_rc():
    rc = config.rc()
    log.debug("reading configuration from: " + rc)
    if not os.path.isfile(rc):
        return None, []

    data = None
    with open(rc, 'r') as f:
        data = json.loads(f.read())

    if _JSON_KEY_REPOSITORY in data:
        ref_store_path = data[_JSON_KEY_REPOSITORY]
        if not _is_valid_repo_path(ref_store_path):
            raise IOError(_ERROR_INVALID_REPOSITORY_PATH)
    else:
        ref_store_path = None
    
    if _JSON_KEY_REFS in data:
        refs = data[_JSON_KEY_REFS]
    else:
        refs = []

    log.debug("read repository path: " + ref_store_path)
    return ref_store_path, refs

# must a directory in users home directory
def _is_valid_repo_path(abspath):
    valid = True
    if not abspath.startswith(os.path.expanduser("~")):
        valid = False
    if not os.path.isdir(abspath):
        valid = False
    return valid

def _is_repo_dir_empty(abspath):
    for dirpath, dirnames, files in os.walk(abspath):
        if files:
            return False
    return True

# Writes a config file with pointer to repository. Assumes repository path have been verified for correctness
def _write_rc(path):
    data = {_JSON_KEY_REPOSITORY: path, _JSON_KEY_REFS: []}
    encoded = json.dumps(data)
    rc = config.rc()
    log.debug("writing run configuration to: " + rc + " with repository path: " + path)
    with open(rc, 'w') as f:
        f.write(encoded)


class RefStore:

    # constructor that assumes trakk is initialized
    def __init__(self):
        self.repo, self.index = read_rc()

    # TODO: add functionality for init into an already existing (ask for confirmation)
    # constructor for inilizing a brand new store
    @classmethod
    def new(self, path):
        log.debug("setting up new RefStore..")
        repo_abs_path = os.path.abspath(path)

        if not os.path.exists(repo_abs_path):
            log.debug("creating missing directories..")
            os.makedirs(repo_abs_path)

        if not _is_valid_repo_path(repo_abs_path):
            raise IOError(_ERROR_INVALID_REPOSITORY_PATH)

        if not _is_repo_dir_empty(repo_abs_path):
            raise IOError(_ERROR_REPOSITORY_NOT_EMPTY)
        
        _write_rc(repo_abs_path)
        return RefStore()


    def check_valid(self):
        if not self.repo:
            raise IOError(_ERROR_NOT_INITIALIZED)
        return True

    def get_repository(self):
        self.check_valid()
        return self.repo

    # assumes path is resolved
    def add_ref(self, path):
        self.check_valid()
        if path in self.index:
            raise exceptions.IOError(RefStore.__ERROR_ALREADY_TRACKED)
        else:
            self.index.append(path)
            self.commit()

    # assumes path is resolved
    def remove_ref(self, path):
        self.check_valid()
        if path in self.index:
            self.index.remove(path)
            self.commit()
        else:
            raise exceptions.IOError(RefStore.__ERROR_NOT_TRACKED)

    def contains_ref(self, path):
        self.check_valid()
        # special case: index file itself is part of repo but should not be part of used index
        if path == config.index_filename():
            return True

        exists = False
        for ref in self.index:
            if ref == path:
                exists = True
                break
        return exists

    def get_index(self):
        self.check_valid()
        return self.index

    def commit(self):
        self.check_valid()
        self.index.sort()
        data = {RefStore.__JSON_KEY_REFS: self.index}
        encoded = json.dumps(data)
        rc = config.index(self.repo)
        with open(rc, 'w') as f:
            f.write(encoded)
