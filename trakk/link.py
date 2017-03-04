# author: Samuel Wejeus (samuel@isalldigital.com)
import os
import log

# Links must be hard links in order to harness the power of inodes!


# TODO handle linking of existing files! (for sync)

class Linker:

    def __init__(self, repository):
        self.repository = repository

    def link(self, src, dest):
        if self.unlink(dest):
            log.info("re:syncing link: {0}".format(src))
        else:
            log.inof("creating new link: {0}".format(src))
        abs_dest = os.path.join(self.repository, dest)
        self.make_dirs_if_needed(abs_dest)
        os.link(src, abs_dest)

    def unlink(self, dest):
        abs_dest = os.path.join(self.repository, dest)
        wasUnlinked = True
        try:
            os.remove(abs_dest)
            wasUnlinked = True
        except OSError:
            wasUnlinked = False
        return wasUnlinked

    def make_dirs_if_needed(self, abs_path):
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