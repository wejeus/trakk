# author: Samuel Wejeus (samuel@isalldigital.com)
import os
import log

# A pathspec is a path
# A pathspec convenience wrapper class for file paths.
# Does not guarantee file exists

# a <ref> is the name of a symbol relative a users home dir (including subfolders)
# a <path> is the full absolute filesystem path for a symbol
# a <ref, path> could be either a file or dir (indicated by trailig "/")

# only cares about creating a pathspec, does not have any oppinion if the 
# path choice is good or not. For example adding "~/" directly or any other dir with many files

_ERROR_NOT_PATHSPEC_TYPE = "invalid type, must be of type Pathspec"

class Pathspec:

    # The constructor needs a real <path> that points to an existing file located under users home dir
    def __init__(self, path: str):
        if path.startswith("~"):
            path = os.path.expanduser(path)
        
        abspath = os.path.abspath(path)
        if os.path.isdir(abspath):
            abspath = abspath + "/"
            log.debug("{0} resolved as directory".format(abspath))
        userpath = os.path.expanduser("~")

        if not abspath.startswith(userpath):
            raise IOError("Path not located under users home (~/): {0}".format(abspath))

        self.abspath = abspath
        self.userpath = userpath
        log.debug("Built pathspec: {0}".format(self.abspath))

    def __repr__(self) -> str:
        return self.abspath

    def is_dir_ref(self) -> bool:
        isDir = os.path.isdir(self.abspath)
        log.debug("{0} is dir? {1}".format(self.abspath, isDir))
        return isDir

    def get_abs_path(self) -> str:
        return self.abspath
    
    # the ref format stored in index. Example of ref: "git/private/system/Library/.DS_Store"
    def get_ref(self) -> str:
        ref = os.path.relpath(self.abspath, self.userpath)
        if os.path.isdir(self.abspath):
            ref = ref + "/"
        return ref

    def get_ref_dirs(self) -> str:
        return os.path.dirname(self.get_ref())

    # use to check if file exist in filesystem outside of repo
    def is_existing_file(self) -> bool:
        return os.path.exists(self.abspath)

    # def ref_name(self, repo):
    #     return self.parse_ref_name(repo, self)

    # TODO migrate away from static and add typehint to pathspec
    @staticmethod
    def get_ref_from_repo(repo, pathspec) -> str:
        assert type(pathspec) is Pathspec, _ERROR_NOT_PATHSPEC_TYPE
        user_rel_repo = repo[len(os.path.expanduser("~")):]
        path = pathspec.get_abs_path()[len(os.path.expanduser("~")):]
        if path.startswith(user_rel_repo):
            path = path[len(user_rel_repo):]
        if path.startswith("/"):
            path = path[1:]
        return path
