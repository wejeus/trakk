# author: Samuel Wejeus (samuel@isalldigital.com)
import os

# A pathspec is a path
# A pathspec convenience wrapper class for file paths.

class Pathspec:

    # The constructor needs a real <path> that points to an existing file located under users home dir
    def __init__(self, path):
        abspath = os.path.abspath(path)
        if not os.path.isfile(abspath):
            raise exceptions.IOError("No such file: {0}".format(abspath))
        if not abspath.startswith(os.path.expanduser("~")):
            raise exceptions.IOError("Path not located under users home (~/): {0}".format(abspath))
        self.abspath = abspath

    def get_abs_path(self):
        return self.abspath

    def get_user_rel_ref(self):
        path = self.abspath
        return os.path.relpath(path, os.path.expanduser("~"))

    def get_ref_path_dirs_only(self):
        return os.path.dirname(self.get_user_relative_path())

    def is_existing_file(self):
        return os.path.exists(self.abspath)
