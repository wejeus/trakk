# author: Samuel Wejeus (samuel@isalldigital.com)
import os
import log
from pathspec import Pathspec
# from types import type

# Links must be hard links in order to harness the power of inodes!

# TODO handle linking of existing files! (for sync)

_ERROR_NOT_PATHSPEC = "target must be of type Pathspec"

# Note: src and dest must be of pathspec type!
class Linker:

    def __init__(self, repository):
        self.repo = repository

    # a link requires src and destination but since we link an existing 
    # file under a new location (but with same relative path) one pathspec
    # is enough to determine linking
    def link(self, pathspec):
        assert type(pathspec) is Pathspec, _ERROR_NOT_PATHSPEC
        log.info("creating link: {0}".format(pathspec))
        # handle empty dir
        self.make_dirs_if_needed(pathspec)
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

    def make_dirs_if_needed(self, pathspec):
        abs_path = os.path.join(self.repo, pathspec.get_user_rel_ref())
        dir_path = os.path.dirname(abs_path)
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)


class BrokenRefType:

    def __init__(self, named_type, reason, ref, mine, theirs):
        self.type = named_type
        self.reason = reason
        self.ref = ref
        self.mine = mine
        self.theirs = theirs

    @staticmethod
    def A(ref, mine, theirs):
        return BrokenRefType("A", "has changes not committed to version control", ref, mine, theirs)

    @staticmethod
    def B(ref, mine, theirs):
        return BrokenRefType("B", "inode mismatch for ref", ref, mine, theirs)

    @staticmethod
    def C(ref, mine, theirs):
        return BrokenRefType("C", "ref does not exist in repository but is present in system", ref, mine, theirs)

    @staticmethod
    def D(ref, mine, theirs):
        return BrokenRefType("D", "new (non existing) upstream ref", ref, mine, theirs)

    @staticmethod
    def E(ref, mine, theirs):
        return BrokenRefType("E", "ref does not exist in either repository OR system", ref, mine, theirs)

    @staticmethod
    def F(ref):
        return BrokenRefType("F", "untracked file", ref, None, None)

    # def mine(self):
    #     return self.my_ref
    #
    # def theirs(self):
    #     return self.their_ref
    #
    # def reason(self):
    #     return self.reason
    #
    # def type(self):
    #     return self.named_type