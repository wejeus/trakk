# author: Samuel Wejeus (samuel@isalldigital.com)
import os

# Assuming HARD links for all link handling!


class Linker:

    def __init__(self, repository):
        self.repository = repository

    def link(self, src, dest):
        if self.unlink(dest):
            print "re:syncing link: {0}".format(src)
        else:
            print "creating new link: {0}".format(src)
        abs_dest = os.path.join(self.repository, dest)
        self.make_dirs_if_needed(abs_dest)
        os.link(src, abs_dest)

    def unlink(self, dest):
        abs_dest = os.path.join(self.repository, dest)
        wasUnlinked = None
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
