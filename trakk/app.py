# author: Samuel Wejeus (samuel@isalldigital.com)

import sys
from pathspec import Pathspec
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

    # remove then add?
    def move(self, src, dest):
        raise Exception("NOT IMPLEMENTED YET!")

    def add(self, params):
        pathspecs = params
        resolved = []
        for ps in pathspecs:
            try:
                resolved.append(Pathspec(ps))
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
                resolved.append(Pathspec(ps))
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
        git_diff_refs = [item.a_path for item in self.git_repo.index.diff(None)] + [item.a_path for item in self.git_repo.index.diff("HEAD")]
        # Handle cases tracked by INDEX
        for ref_name in self.storage.get_index():
            status = self.determine_link_status(ref_name)
            if ref_name in git_diff_refs:
                git_diff_refs.remove(ref_name)
            if status:
                broken_refs.append(status)

        # Handle dangling files NOT tracked by index
        repo = self.storage.get_repository()
        for root, dirs, files in os.walk(repo):
            for file in files:
                ref_name = os.path.join(root, file).split(repo + "/")[1]
                status = self.determine_track_status(ref_name)
                if status:
                    broken_refs.append(status)

        # Handle git specific case where file is intentionally unknown to trakk (dangling git index)
        # i.e. file not index and not in repository but known to git (either staged or not)
        # Example file staged for deletion in git but not commited as a result of a --remove operation
        for ref_name in git_diff_refs:
            mine, theirs = self.mine_theirs_from_ref(ref_name)
            broken_refs.append(link.BrokenRefType.A(mine, theirs))

        return broken_refs

    def status(self, params=None):
        log.info("{0} repository: {1}".format(config.APP, self.storage.get_repository()))
        broken_refs = self.get_broken_refs()
        if len(broken_refs) > 0:
            # broken_refs.sort(key=lambda tup: tup[1]) throws "instance has no attribute '__getitem__'" since no longer tuple
            log.info("\nFound broken or inconsistent refs:")
            sorted_refs = sorted(broken_refs, key=lambda ref: ref.type) 
            printed_headlines = []
            for broken_ref in sorted_refs:
                if not broken_ref.type in printed_headlines:
                    log.info("\n{0} (type {1})".format(broken_ref.reason, broken_ref.type))
                    printed_headlines.append(broken_ref.type)

                if broken_ref.type == "A":
                    log.info(broken_ref.mine)
                elif broken_ref.type == "B":
                    log.info("mine: {0} -> theirs: {1}".format(broken_ref.mine, broken_ref.theirs))
                elif broken_ref.type == "C":
                    log.info(broken_ref.mine)
                elif broken_ref.type == "D":
                    log.info(broken_ref.theirs)
                elif broken_ref.type == "E":
                    log.info(broken_ref.mine) # neither exist but pick a name for display
                elif broken_ref.type == "F":
                    log.info(broken_ref.theirs)
            return True
        else:
            log.info("All OK")
        return False

    def mine_theirs_from_ref(self, ref):
        mine = os.path.join(os.path.expanduser("~"), ref) # R
        theirs = os.path.join(self.storage.get_repository(), ref) # L
        return mine, theirs

    # determines tracked status of a path like name. That is a ref relative <repository>
    def determine_track_status(self, ref_name):
        if ref_name.startswith('.git/'):
            return None
        log.debug("determine track status for: {0}".format(ref_name))
        repo = self.storage.get_repository()
        theirs_ps = Pathspec(os.path.join(repo, ref_name))
        if not self.storage.contains_ref(theirs_ps):
            return link.BrokenRefType.F(theirs_ps.get_abs_path())
        return None

    def determine_link_status(self, ref):
        mine, theirs = self.mine_theirs_from_ref(ref)

        # Case C, E
        if not os.path.exists(theirs):
            if os.path.exists(mine):
                return link.BrokenRefType.C(mine, theirs)
            else:
                return link.BrokenRefType.E(mine, theirs)
        # Case A, B, D (theirs do exist)
        else:
            # Case D
            if not os.path.exists(mine):
                return link.BrokenRefType.D(mine, theirs)
            # Case A, B (mine do exist)
            else:
                if os.path.samefile(mine, theirs):
                    # theirs, mine points to same inode, link is OK but could still diff from what is in git db
                    if ref in self.git_repo.untracked_files or self.git_repo.head.commit.diff(None, paths=ref):
                        return link.BrokenRefType.A(mine, theirs)
                else:
                    return link.BrokenRefType.B(mine, theirs)
        return None

    # diff for cases A, B
    def show(self, params):
        if len(params) != 1:
            log.error("can only handle one ref at a time")
            sys.exit(1)

        ref = Pathspec.parse_ref_name(self.storage.get_repository(), Pathspec(params[0]))
        ref = os.path.join(self.storage.get_repository(), ref)

        log.debug("determine show for: " + ref)
        status = self.determine_track_status(ref)
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
                log.info("Untracked file. Nothing to show.")
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

    # NOTE: sync always linked in direction from <system> to <repository> (by force)
    # commiting to verson control is NOT handled by sync. We hand that off to interacting with git directly
    def sync(self, params=None):
        self.sync_internal(self.get_broken_refs())

    def sync_internal(self, refs=None):
        if not refs:
            return

        for broken_ref in refs:
            if broken_ref.type == "B":
                self.sync_choose_which(broken_ref.mine, broken_ref.theirs)
            elif broken_ref.type == "C":
                self.sync_add(broken_ref.mine)
            elif broken_ref.type == "D":
                self.linker.link_raw(broken_ref.theirs, broken_ref.mine)
            elif broken_ref.type == "E":
                self.sync_remove_from_index(broken_ref.mine)
            elif broken_ref.type == "F":
                ps = Pathspec(broken_ref.theirs)
                self.storage.add_ref(ps)
            elif broken_ref.type == "A":
                # do this last since we only want to commit data when in a clean state
                continue
            else:
                raise Exception("unknown broken ref type: {0}".format(broken_ref))
            # continue rotation of fixing this perticular ref if more actions are needed
            # self.sync_internal([self.determine_link_status(broken_ref.ref)])

    def sync_remove_from_index(self, mine):
        ref_name = mine[len(os.path.expanduser("~")):]
        if ref_name.startswith("/"):
            ref_name = ref_name[1:]
        log.info("Ref '{0}' is only present as a name in index (file does not exist in either system or repository). Should I remove it from the index? (Y)es/(N)o/(S)kip: ".format(ref_name))
        choice = sys.stdin.readline().rstrip().lower()
        if choice == "s":
            return False
        if choice == "y":
            self.storage.remove_ref_raw(ref_name)
            return True
        if choice == "n":
            return False
        else:
            print("What?")
            return self.sync_remove_from_index(mine)

    def sync_add(self, mine):
        log.info("Ref '{0}' exists in system and index but is not linked to repository. Should I add it? (Y)es/(N)o/(S)kip: ".format(mine))
        choice = sys.stdin.readline().rstrip().lower()
        if choice == "s":
            return False
        if choice == "y":
            self.linker.link(Pathspec(mine))
            return True
        if choice == "n":
            return False
        else:
            print("What?")
            return self.sync_add(mine)

    def sync_choose_which(self, mine, theirs):
        ref = mine
        log.info("Unresolvable file conflict for '{0}' (exists both in system and repository). Which should I pick? (M)ine/(T)heirs/(S)kip: ".format(ref))
        choice = sys.stdin.readline().rstrip().lower()
        if choice == "s":
            return False
        if choice == "m":
            self.linker.link_raw(mine, theirs, True)
            return True
        if choice == "t":
            self.linker.link_raw(theirs, mine, True)
            return True
        else:
            print("What?")
            return self.sync_choose_which(mine, theirs)

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
                pathspecs.append(Pathspec(ps))
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

