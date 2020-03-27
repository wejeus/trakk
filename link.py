# author: Samuel Wejeus (samuel@isalldigital.com)
import os
import log
from pathspec import Pathspec
# from types import type

# Links must be hard links in order to harness the power of inodes!

# TODO handle linking of existing files! (for sync)

_ERROR_NOT_PATHSPEC = "target must be of type Pathspec"
_ERROR_INVALID_USER_ABS_PATH = "target must be an absolute path rooted in user home dir"

# Note: src and dest must be of pathspec type!
class Linker:

    def __init__(self, repository):
        self.repo = repository

    # src, dest must be absolute paths
    def link_raw(self, src, dest, forced=False):
        assert src.startswith(os.path.expanduser("~")), _ERROR_INVALID_USER_ABS_PATH
        assert dest.startswith(os.path.expanduser("~")), _ERROR_INVALID_USER_ABS_PATH
        # handle missing parent dirs
        self.make_dirs_if_needed(dest)
        if forced:
            os.remove(dest)
        os.link(src, dest)

    # a link requires src and destination but since we link an existing 
    # file under a new location (but with same relative path) one pathspec
    # is enough to determine linking
    def link(self, pathspec):
        assert type(pathspec) is Pathspec, _ERROR_NOT_PATHSPEC
        log.info("creating link: {0}".format(pathspec))
        # handle missing parent dirs
        self.make_dirs_if_needed(os.path.join(self.repo, pathspec.get_user_rel_ref()))
        path_in_repo = os.path.join(self.repo, pathspec.get_user_rel_ref())
        os.link(pathspec.get_abs_path(), path_in_repo)

    # unlinking is a basic removal of file. This will handle 2 cases:
    # both if the file is actually linked (2 files point to same inode)
    # of if file is out of sync and has no target. In both cases the file
    # in the repo dir is removed.
    def unlink(self, dest):
        assert type(dest) is Pathspec, _ERROR_NOT_PATHSPEC
        log.debug("Unlinking: {0}".format(dest.get_abs_path()))
        name = Pathspec.parse_ref_name(self.repo, dest)
        path = os.path.join(self.repo, name)
        wasUnlinked = True
        try:
            os.remove(path)
            wasUnlinked = True
        except OSError:
            wasUnlinked = False
        return wasUnlinked

    def make_dirs_if_needed(self, path):
        assert path.startswith(os.path.expanduser("~")), _ERROR_INVALID_USER_ABS_PATH
        dir_path = os.path.dirname(path)
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)


# <mine> is what is located in your local fs, <theirs> refers to something located in <repository>
class BrokenRefType:

    # TODO: migrate ref (and maybe mine/theirs) to pathspecs
    def __init__(self, named_type, reason, mine, theirs):
        self.type = named_type
        self.reason = reason
        self.mine = mine
        self.theirs = theirs

    def __repr__(self):
        return "BrokenRef: type {0} mine {1} theirs {2}".format(self.type, self.mine, self.theirs)

    @staticmethod
    def A(mine, theirs):
        return BrokenRefType("A", "Has changes not committed to version control", mine, theirs)

    @staticmethod
    def B(mine, theirs):
        return BrokenRefType("B", "Inode mismatch for ref", mine, theirs)

    @staticmethod
    def C(mine, theirs):
        return BrokenRefType("C", "Ref does not exist in repository but is present in system", mine, theirs)

    @staticmethod
    def D(mine, theirs):
        return BrokenRefType("D", "New incoming (non existing in system) upstream ref", mine, theirs)

    @staticmethod
    def E(mine, theirs):
        return BrokenRefType("E", "Ref does not exist in either repository OR system", mine, theirs)

    @staticmethod
    def F(theirs):
        return BrokenRefType("F", "Untracked file", None, theirs)