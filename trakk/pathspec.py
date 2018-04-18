# author: Samuel Wejeus (samuel@isalldigital.com)
import os

# A pathspec is a path
# A pathspec convenience wrapper class for file paths.

class Pathspec:

    # The constructor needs a real <path> that points to an existing file located under users home dir
    def __init__(self, path):
        if path.startswith("~"):
            path = os.path.expanduser(path)

        abspath = os.path.abspath(path)

        if not os.path.isfile(abspath):
            raise IOError("No such file: {0}".format(abspath))
        if not abspath.startswith(os.path.expanduser("~")):
            raise IOError("Path not located under users home (~/): {0}".format(abspath))
        self.abspath = abspath

    def __repr__(self):
        return self.abspath

    def get_abs_path(self):
        return self.abspath

    # the ref format stored in index. Example of ref: "git/private/system/Library/.DS_Store"
    def get_user_rel_ref(self):
        return os.path.relpath(self.abspath, os.path.expanduser("~"))

    def get_ref_path_dirs_only(self):
        return os.path.dirname(self.get_user_rel_ref())

    # use to check if file exist in filesystem outside of repo
    def is_existing_file(self):
        return os.path.exists(self.abspath)

    @staticmethod
    def parse_ref_name(repo, pathspec):
        assert type(pathspec) is Pathspec, _ERROR_NOT_PATHSPEC
        user_rel_repo = repo[len(os.path.expanduser("~")):]
        path = pathspec.get_abs_path()[len(os.path.expanduser("~")):]
        if path.startswith(user_rel_repo):
            path = path[len(user_rel_repo):]
        if path.startswith("/"):
            path = path[1:]
        return path
