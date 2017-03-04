# author: Samuel Wejeus (samuel@isalldigital.com)
import os
import json
import exceptions
import config
import log

# a <ref> is pointer to a local file given by its <user_home> relative path.
# Example: "<track dir>/.gitconfig is the ref to the real file ~/.gitconfig
# but normalized relative to track dir. That is is the track dir is omitted and result is just .gitconfig.
# All files are (unless defined explicitly defined in config) assumed to be relative home dir (~/)

# STORAGE
#
# Storage consists of, and handles, a <rc> and <index> file located in <user home> and <repo> respectively
# The <rc> holds a pointer to the repo and other potential configs for Trakk in general
# The <index> is and index if traked files and is intended to be part of the version controled files

# <rc> have to look like this: {"repository": "/Users/sawe/git/isalldigital.com/system"} (using absolute paths)


class Storage:

    __ERROR_NOT_INITIALIZED = "Invalid repository and/or path"
    __ERROR_INVALID_REPOSITORY_PATH = "Repository path must already exist and be a sub folder to users home directory"
    __ERROR_NOT_TRACKED = "File not tracked"
    __ERROR_ALREADY_TRACKED = "File already tracked"
    __ERROR_REPOSITORY_NOT_EMPTY = "Specified repository path is not empty and/or already exists"

    __JSON_KEY_REPOSITORY = 'repository'
    __JSON_KEY_REFS = 'refs'

    @classmethod
    def new(cls, path, create_index=True):
        log.debug("setting up new storage..")
        repo_abs_path = os.path.abspath(path)
        if not Storage.__is_valid_repo_path(repo_abs_path):
            raise exceptions.IOError(Storage.__ERROR_INVALID_REPOSITORY_PATH)

        if not Storage.__is_repo_dir_empty(repo_abs_path):
            raise exceptions.IOError(Storage.__ERROR_REPOSITORY_NOT_EMPTY)

        Storage.__write_rc(repo_abs_path)

        if create_index:
            log.debug("creating new index..")
            if not os.path.exists(repo_abs_path):
                log.debug("creating missing directories..")
                os.makedirs(repo_abs_path)
            
            Storage.__write_index(repo_abs_path)

    # Writes a config file with pointer to repository. Assumes repository path have been verified for correctness
    @staticmethod
    def __write_rc(path):
        data = {Storage.__JSON_KEY_REPOSITORY: path}
        encoded = json.dumps(data)
        rc = config.rc()
        log.debug("writing run configuration to: " + rc + " with repository path: " + path)
        with open(rc, 'w') as f:
            f.write(encoded)

    # returns valid (repository) or throw
    @staticmethod
    def __read_rc():
        rc = config.rc()
        log.debug("reading run configuration from: " + rc)
        data = None
        with open(rc, 'r') as f:
            data = json.loads(f.read())

        path = data[Storage.__JSON_KEY_REPOSITORY]
        if not Storage.__is_valid_repo_path(path):
            raise exceptions.IOError(Storage.__ERROR_NOT_INITIALIZED)
        log.debug("read repository path: " + path)

        return path

    @staticmethod
    def __write_index(path):
        data = {Storage.__JSON_KEY_REFS: []}
        encoded = json.dumps(data)
        index = config.index(path)
        log.debug("writing empty index to: " + index)
        with open(index, 'w') as f:
            f.write(encoded)
    
    @staticmethod
    def __read_index(path):
        index = config.index(path)
        log.debug("reading index from: " + index)
        data = None
        with open(index, 'r') as f:
            data = json.loads(f.read())

        refs = data[Storage.__JSON_KEY_REFS]
        return refs

    @staticmethod
    def __is_repo_dir_empty(abspath):
        for dirpath, dirnames, files in os.walk(abspath):
            if files:
                return False
        return True

    # must a directory in users home directory
    @staticmethod
    def __is_valid_repo_path(abspath):
        valid = True
        if not abspath.startswith(os.path.expanduser("~")):
            valid = False

        if os.path.isfile(abspath):
            valid = False

        return valid

    def __init__(self):
        self.repo = Storage.__read_rc()
        self.index = Storage.__read_index(self.repo)

    def get_repository(self):
        return self.repo

    # assumes path is resolved
    def add_ref(self, path):
        if path in self.index:
            raise exceptions.IOError(Storage.__ERROR_ALREADY_TRACKED)
        else:
            self.index.append(path)
            self.commit()

    # assumes path is resolved
    def remove_ref(self, path):
        if path in self.index:
            self.index.remove(path)
            self.commit()
        else:
            raise exceptions.IOError(Storage.__ERROR_NOT_TRACKED)

    def contains_ref(self, path):
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
        return self.index

    def commit(self):
        self.index.sort()
        data = {Storage.__JSON_KEY_REFS: self.index}
        encoded = json.dumps(data)
        rc = config.index(self.repo)
        with open(rc, 'w') as f:
            f.write(encoded)
