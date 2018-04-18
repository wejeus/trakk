# author: Samuel Wejeus (samuel@isalldigital.com)

import sys
import pathspec
import os
import config
import log
import link

AVAILABLE_ACTIONS = ["list", "status", "sync", "add", "remove", "restore", "show"]

class App:
    def __init__(self, ref_storage, linker, git_repo):
        self.storage = ref_storage
        self.linker = linker
        self.git_repo = git_repo

    def add(self, params):
        pathspecs = params
        resolved = []
        for ps in pathspecs:
            try:
                resolved.append(pathspec.Pathspec(ps))
            except Exception as e:
                log.error(e)
                return

        for ps in resolved:
            if self.storage.contains_ref(ps): # and os.path.isfile(ps.get_abs_path()):
                log.info("File already tracked: {0}".format(ps))
                continue
            self.storage.add_ref(ps)  # best to save ref first if something goes wrong later
            self.linker.link(ps)

    # can be used to either remove a ref pointed to by path in repo dir
    # or by pointing to original source file. Either way refs are remove
    # and (maybe) unlinked if needed.
    def remove(self, pathspecs):
        resolved = []
        for ps in pathspecs:
            try:
                resolved.append(pathspec.Pathspec(ps))
            except Exception as e:
                log.error(e)
                return
        for ps in resolved:
            log.debug("Removing ref: {0}".format(ps))
            try:
                self.storage.remove_ref(ps)
            except Exception as e:
                pass
            self.linker.unlink(ps)

    def list(self, params=None):
        log.info("Tracking files:")
        refs = self.storage.get_index()
        if not refs:
            log.info("None")
            return
        for ref in refs:
            log.info('~/' + ref)

    def get_broken_refs(self):
        broken_refs = []

        # Handle cases tracked by INDEX
        for ref in self.storage.get_index():
            status = self.determine_link_status(ref)
            if status:
                broken_refs.append(status)

        # Handle dangling files NOT tracked by index
        for root, dirs, files in os.walk(self.storage.get_repository()):
            for name in files:
                ref = os.path.join(root, name).split(self.storage.get_repository() + "/")[1]
                status = self.determine_untracked_status(ref)
                if status:
                    broken_refs.append(status)

        return broken_refs

    def status(self, params=None):
        log.info("{0} repository: {1}".format(config.APP, self.storage.get_repository()))

        broken_refs = self.get_broken_refs()

        if len(broken_refs) > 0:
            # broken_refs.sort(key=lambda tup: tup[1]) throws "instance has no attribute '__getitem__'" since no longer tuple
            log.info("Found broken refs:")
            for broken_ref in broken_refs:
                log.info("{0}: {1} (type {2})".format(broken_ref.reason, broken_ref.ref, broken_ref.type))
            return True
        else:
            log.info("All OK")

        return False

    def determine_untracked_status(self, ref):
        if ref.startswith('.git/'):
            return None
        if not self.storage.contains_ref(ref):
            return link.BrokenRefType.F(ref)
        return None

    def determine_link_status(self, ref):
        R = os.path.join(os.path.expanduser("~"), ref)
        L = os.path.join(self.storage.get_repository(), ref)

        # Case C, E
        if not os.path.exists(L):
            if os.path.exists(R):
                return link.BrokenRefType.C(ref, L, R)
            else:
                return link.BrokenRefType.E(ref, L, R)
        # Case A, B, D (L do exist)
        else:
            # Case D
            if not os.path.exists(R):
                return link.BrokenRefType.D(ref, L, R)
            # Case A, B (R do exist)
            else:
                if os.path.samefile(R, L):
                    # L, R points to same inode, link is OK but could still diff from what is in git db
                    if self.git_repo.head.commit.diff(None, paths=ref):
                        return link.BrokenRefType.A(ref, L, R)
                else:
                    return link.BrokenRefType.B(ref, L, R)

        return None

    # diff for cases A, B
    def show(self, params):
        if len(params) != 1:
            log.error("can only handle one ref at a time")
            sys.exit(1)

        ref = params[0]
        log.debug("determine show for: " + ref)

        status = self.determine_untracked_status(ref)

        if not status:
            status = self.determine_link_status(ref)

        if status:
            if status.type == "A":
                for diff in self.git_repo.head.commit.diff(None, paths=status.mine, create_patch=True):
                    log.info(diff)
            elif status.type == "B":
                self.show_file_diff(status.mine, status.theirs)
            elif status.type == "C":
                self.show_file_diff(None, status.theirs)
            elif status.type == "D":
                self.show_file_diff(status.mine, None)
            elif status.type == "E":
                log.info(status.reason)
            elif status.type == "F":
                log.info("Untracked file. Nothing to show. Does not exist in neither index or system.")
            else:
                log.error("unknown status!")
        else:
            log.info(ref + " ... OK")

    def show_file_diff(self, L, R):
        if L:
            log.info("Mine: {0}".format(L))
            log.info("=======================================================")
            with open(L, 'r') as fin:
                log.info(fin.read())
        else:
            log.info("=======================================================")
            log.info("<ref not present in index>")

        if R:
            log.info("Theirs: {0}".format(R))
            log.info("=======================================================")
            with open(R, 'r') as fin:
                log.info(fin.read())
        else:
            log.info("=======================================================")
            log.info("<ref not present in system>")

    # NOTE: sync always goes from SYSTEM to REPO (by force)
    def sync(self, params=None):

        for broken_ref in self.get_broken_refs():
            if broken_ref.type == "B":
                self.sync_choose_which(broken_ref.ref, broken_ref.mine, broken_ref.theirs)

        # for root, dirs, files in os.walk(self.storage.get_repository()):
        #     for name in files:
        #         ref = os.path.join(root, name).split(self.storage.get_repository() + "/")[1]
        #         if ref.startswith('.git'):
        #             continue
        #         if not self.storage.contains_ref(ref):
        #             pathspecs.append(pathspec.Pathspec(os.path.join(home, ref)))
        #
        # for ps in pathspecs:
        #     self.linker.link(ps.get_abs_path(), ps.get_user_rel_ref())
        #     if not self.storage.contains_ref(ps.get_user_rel_ref()):
        #         self.storage.add_ref(ps.get_user_rel_ref())

    def sync_choose_which(self, ref, mine, theirs):
        sys.stdout.write("{0} pick (M)ine/(T)heirs/(S)kip: ".format(ref))
        choice = sys.stdin.readline().rstrip().lower()
        if choice == "s":
            return False
        if choice == "m":
            link.link(mine, theirs)
            return True
        if choice == "t":
            link.link(theirs, mine)
            return True
        else:
            print("What?")
            return self.sync_choose_which(ref, mine, theirs)

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
            except Exception as e:
                print(e)
                sys.exit(1)

        for ps in pathspecs:
            system_abs_path = ps.get_abs_path()
            track_ref_path = ps.get_user_rel_ref()
            track_abs_path = os.path.join(self.storage.get_repository(), track_ref_path)
            if not self.storage.contains_ref(ps.get_user_rel_ref()):
                print("File not tracked (use --add <pathspec> to start tracking): {0}".format(ps.get_abs_path()))
                sys.exit(1)
            # inode mismatch, restore by linking in opposite direction
            if not os.path.samefile(system_abs_path, track_abs_path):
                os.remove(system_abs_path)
                os.link(track_abs_path, system_abs_path)
                continue
            if self.git_repo.index.checkout(paths=track_abs_path, force=True):
                os.remove(system_abs_path)
                os.link(track_abs_path, system_abs_path)
                continue