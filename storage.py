# author: Samuel Wejeus (samuel@isalldigital.com)
import os
import json
import exceptions
import config

# a ref is the track dir local reference, example <track dir>/.gitconfig is the ref to the real file ~/.gitconfig
# but normalized relative to track dir. That is is the track dir is omitted and result is just .gitconfig.
# All files are (unless defined explicitly defined in config) assumed to be relative home dir (~/)


class Storage:

    __ERROR_NOT_INITIALIZED = "Invalid repository and/or path"
    __ERROR_INVALID_REPOSITORY_PATH = "Repository path must already exist and be a sub folder to users home directory"
    __ERROR_NOT_TRACKED = "File not tracked"
    __ERROR_ALREADY_TRACKED = "File already tracked"
    __ERROR_REPOSITORY_NOT_EMPTY = "Specified repository path is not empty"

    __JSON_KEY_REPOSITORY = 'repository'
    __JSON_KEY_REFS = 'refs'

    # should throw on: non empty dir
    @classmethod
    def new(cls, path):
        abspath = os.path.abspath(path)
        if not Storage.__is_valid_repository_path(abspath):
            raise exceptions.IOError(Storage.__ERROR_INVALID_REPOSITORY_PATH)

        if not Storage.__is_repository_dir_empty(abspath):
            raise exceptions.IOError(Storage.__ERROR_REPOSITORY_NOT_EMPTY)

        Storage.__create_empty_config_file(abspath)

    @staticmethod
    def __create_empty_config_file(abspath):
        data = {Storage.__JSON_KEY_REPOSITORY: abspath, Storage.__JSON_KEY_REFS: []}
        encoded = json.dumps(data)
        rc = os.path.join(os.path.expanduser("~"), config.RC_FILENAME)
        with open(rc, 'w') as f:
            f.write(encoded)

    # returns valid (repository, refs) or throw
    @staticmethod
    def __read_config():
        rc = os.path.join(os.path.expanduser("~"), config.RC_FILENAME)
        data = None
        with open(rc, 'r') as f:
            data = json.loads(f.read())

        repository = os.path.expanduser(data[Storage.__JSON_KEY_REPOSITORY])
        if not Storage.__is_valid_repository_path(repository):
            raise exceptions.IOError(Storage.__ERROR_NOT_INITIALIZED)

        refs = []
        if Storage.__JSON_KEY_REFS in data:
            refs = data[Storage.__JSON_KEY_REFS]
            refs.sort()
        return repository, refs

    @staticmethod
    def __is_repository_dir_empty(abspath):
        for dirpath, dirnames, files in os.walk(abspath):
            if files:
                return False
        return True

    # must a directory in users home directory
    @staticmethod
    def __is_valid_repository_path(abspath):
        valid = True
        if not abspath.startswith(os.path.expanduser("~")):
            valid = False
        if not os.path.isdir(abspath):
            valid = False

        return valid

    def __init__(self):
        self.repository, self.refs = Storage.__read_config()

    # returns abspath to repository
    def get_repository(self):
        return self.repository

    # assumes path is resolved
    def add_ref(self, path):
        if path in self.refs:
            raise exceptions.IOError(Storage.__ERROR_ALREADY_TRACKED)
        else:
            self.refs.append(path)
            self.commit()

    # assumes path is resolved
    def remove_ref(self, path):
        if path in self.refs:
            self.refs.remove(path)
            self.commit()
        else:
            raise exceptions.IOError(Storage.__ERROR_NOT_TRACKED)

    def contains_ref(self, path):
        exists = False
        for ref in self.refs:
            if ref == path:
                exists = True
                break
        return exists
        # return self.refs[path]?

    def get_refs(self):
        return self.refs

    def commit(self):
        self.refs.sort()
        data = {Storage.__JSON_KEY_REPOSITORY: self.repository, Storage.__JSON_KEY_REFS: self.refs}
        encoded = json.dumps(data)
        home = os.path.expanduser("~")
        rc = os.path.join(home, config.RC_FILENAME)
        with open(rc, 'w') as f:
            f.write(encoded)
