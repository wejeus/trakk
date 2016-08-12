import sys
import pathspec
import os
import config


AVAILABLE_ACTIONS = ["list", "status", "sync", "add", "remove", "restore"]


class Base:
    def __init__(self, ref_storage, linker, git_repo):
        self.storage = ref_storage
        self.linker = linker
        self.repo = git_repo

    def add(self, params):
        pathspecs = params
        resolved = []
        for ps in pathspecs:
            try:
                resolved.append(pathspec.Pathspec(ps))
            except Exception, e:
                print e
                sys.exit(1)

        for ps in resolved:
            self.storage.add_ref(ps.get_ref_path())  # best to save ref first if something goes wrong later
            self.linker.link(ps.get_abs_path(), ps.get_ref_path())

    def remove(self, params):
        pathspecs = params
        resolved = []
        for ps in pathspecs:
            try:
                resolved.append(pathspec.Pathspec(ps))
            except Exception, e:
                print e
                sys.exit(1)

        for ps in resolved:
            self.storage.remove_ref(ps.get_ref_path())
            self.linker.unlink(ps.get_ref_path())

    def list(self, params=None):
        for ref in self.storage.get_refs():
            print '~/' + ref

    def status(self, params=None):
        print "{0} repository: {1}".format(config.APP, self.storage.get_repository())

        err = False
        for unknown_ref in self.repo.untracked_files:
            if not self.storage.contains_ref(unknown_ref):
                print "untracked ref: " + unknown_ref
                err = True

        for ref in self.storage.get_refs():
            system_abs_path = os.path.join(os.path.expanduser("~"), ref)
            track_abs_path = os.path.join(self.storage.get_repository(), ref)
            if not os.path.exists(system_abs_path):
                print "target file does not exists: " + ref
                err = True
                continue
            if not os.path.exists(track_abs_path):
                print "ref file does not exists: " + ref
                err = True
                continue
            if not os.path.samefile(system_abs_path, track_abs_path):
                print "inode mismatch for ref: " + ref
                err = True
                continue
            if self.repo.head.commit.diff(None, paths=ref):
                print "not staged for commit: " + ref
                err = True
                continue
            # files could also be in storage link all good but not added git (will not be detected by diff)

        for root, dirs, files in os.walk("/Users/wejeus/git/system"):
            for name in files:
                ref = os.path.join(root, name).split(self.storage.get_repository() + "/")[1]
                if ref.startswith('.git'):
                    continue
                if not self.storage.contains_ref(ref):
                    print "Not tracked file: " + ref

        return err

    # NOTE: sync always goes from SYSTEM to REPO (by force)
    def sync(self, params=None):
        pathspecs = []
        home = os.path.expanduser("~")
        for ref in self.storage.get_refs():
            print ref
            pathspecs.append(pathspec.Pathspec(os.path.join(home, ref)))

        for root, dirs, files in os.walk("/Users/wejeus/git/system"):
            for name in files:
                ref = os.path.join(root, name).split(self.storage.get_repository() + "/")[1]
                if ref.startswith('.git'):
                    continue
                if not self.storage.contains_ref(ref):
                    pathspecs.append(pathspec.Pathspec(os.path.join(home, ref)))

        for ps in pathspecs:
            self.linker.link(ps.get_abs_path(), ps.get_ref_path())
            if not self.storage.contains_ref(ps.get_ref_path()):
                self.storage.add_ref(ps.get_ref_path())





    # NOTE: restore always goes from REPO to SYSTEM (by force)
    def restore(self, params):
        # for each pathspec, check if exist in Storage else abort (needs ADD)
        # for each pathspec, check if points to same inode if not abort (needs SYNC)
        # check for changes in git if no diff abort (no change detected)
        # restore system file by copying from git repo to system location
        # re:sync path
        paths = params
        pathspecs = []
        for ps in paths:
            try:
                pathspecs.append(pathspec.Pathspec(ps))
            except Exception, e:
                print e
                sys.exit(1)

        for ps in pathspecs:
            system_abs_path = ps.get_abs_path()
            track_ref_path = ps.get_ref_path()
            track_abs_path = os.path.join(self.storage.get_repository(), track_ref_path)
            if not self.storage.contains_ref(ps.get_ref_path()):
                print "File not tracked (use --add <pathspec> to start tracking): {0}".format(ps.get_abs_path())
                sys.exit(1)
            # inode mismatch, restore by linking in opposite direction
            if not os.path.samefile(system_abs_path, track_abs_path):
                os.remove(system_abs_path)
                os.link(track_abs_path, system_abs_path)
                continue
            if self.repo.index.checkout(paths=track_abs_path, force=True):
                os.remove(system_abs_path)
                os.link(track_abs_path, system_abs_path)
                continue