# author: Samuel Wejeus (samuel@isalldigital.com)
import os
import json
import config
import log
from pathspec import Pathspec
from config import Config

# a <ref> is pointer to a local file given by its <user_home> relative path.
# Example: "<track dir>/.gitconfig is the ref to the real file ~/.gitconfig
# but normalized relative to track dir. That is is the track dir is omitted and result is just .gitconfig.
# All files are (unless defined explicitly defined in config) assumed to be relative home dir (~/)

# RefStore - RESPONSIBLE FOR MAINTAINING AN INDEX OF REF'S AND POINT OUT WHERE THE GIT REPOSITORY IS
# 
# Storage consists of, and handles, a <repository> and <index>.
# The <repository> holds a pointer to the repo and other potential configs for Trakk in general
# The <index> is and index if traked files and is intended to be part of the version controled files
# <rc> have to look like this: {"repository": "/Users/sawe/git/isalldigital.com/system"} (using absolute path)
# the refs stored in <index> must be <repository> relative sub paths only since location of <repository> could change.

# +---------------------------------------------+
# | RefStore                                    |
# | +------------------+ +--------------------+ |
# | | Index[Pathspecs] | | Repository         | |
# | +------------------+ +--------------------+ |
# +---------------------------------------------+

_ERROR_NOT_INITIALIZED = "Trakk not yet initialized!"
_ERROR_NOT_TRACKED = "File not tracked"
_ERROR_ALREADY_TRACKED = "File already tracked"
_ERROR_NOT_PATHSPEC = "target must be of type Pathspec"
_ERROR_INVALID_REPOSITORY_PATH_NOT_IN_HOME = "Invalid repository! Repository path must exist and be a subfolder of users home directory"
_ERROR_INVALID_REPOSITORY_PATH_NOT_A_DIR = "Invalid repository! Repository path must exist and must be a directory"

class RefStore:

    def __init__(self, config: Config):
        self.config = config
        self.reload()

    def reload(self):
        self.repo, self.index, self.dirs = self.config.read_rc()

    def check_valid(self):
        if not self.repo:
            raise IOError(_ERROR_NOT_INITIALIZED)
        self.check_repo_valid()

    def check_repo_valid(self):
        # TODO: maybe add check to make sure repository also is a git repository
        if not self.repo.startswith(os.path.expanduser("~")):
            raise IOError(_ERROR_INVALID_REPOSITORY_PATH_NOT_IN_HOME)
        if not os.path.isdir(self.repo):
            raise IOError(_ERROR_INVALID_REPOSITORY_PATH_NOT_A_DIR)
    
    def get_repository(self):
        self.check_valid()
        return self.repo

    # assumes path is resolved
    def add_ref(self, pathspec: Pathspec) -> bool:
        assert type(pathspec) is Pathspec, _ERROR_NOT_PATHSPEC
        self.check_valid()
        name = Pathspec.get_ref_from_repo(self.repo, pathspec)
        if name in self.index:
            return False
        else:
            self.index.append(name)
            self.commit()
        return True

    def add_dir_ref(self, pathspec: Pathspec) -> bool:
        assert type(pathspec) is Pathspec, _ERROR_NOT_PATHSPEC
        self.check_valid()
        if pathspec.is_dir_ref:
            name = Pathspec.get_ref_from_repo(self.repo, pathspec)
            if name in self.dirs:
                return False
            else:
                self.dirs.append(name)
                self.commit()
            return True
        return False
    
    # assumes path is resolved
    def remove_ref(self, pathspec: Pathspec, forced=False) -> bool:
        assert type(pathspec) is Pathspec, _ERROR_NOT_PATHSPEC
        self.check_valid()

        name = pathspec.get_ref()
        if not forced:
            name = Pathspec.get_ref_from_repo(self.repo, pathspec)

        if name in self.index:
            self.index.remove(name)
            self.commit()
            return True
        else:
            return False

    def contains_ref(self, pathspec: Pathspec) -> bool:
        assert type(pathspec) is Pathspec, _ERROR_NOT_PATHSPEC
        self.check_valid()
        name = Pathspec.get_ref_from_repo(self.repo, pathspec)
        exists = False
        for ref in self.index:
            if ref == name:
                exists = True
                break
        log.debug("Contains ref: {0} -> {1}".format(pathspec, exists))
        return exists

    def get_index(self):
        self.check_valid()
        return self.index

    def get_dirs(self):
        self.check_valid()
        return self.dirs

    def commit(self):
        self.check_valid()
        log.error("TODO: Sort refs in ref_store.commit() before saving!")
        self.config.write_rc(self.repo, self.index, self.dirs)

    def is_pathspec_in_repo_dir(self, pathspec: Pathspec) -> bool:
        assert type(pathspec) is Pathspec
        return pathspec.get_abs_path().startswith(self.repo)

