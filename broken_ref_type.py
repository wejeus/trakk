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