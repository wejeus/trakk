import sys
import pathspec
import os
import config
import log

AVAILABLE_ACTIONS = ["list", "status", "sync", "add", "remove", "restore", "show"]


class Base:
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
            except Exception, e:
                print e
                sys.exit(1)

        for ps in resolved:
            self.storage.add_ref(ps.get_user_rel_ref())  # best to save ref first if something goes wrong later
            self.linker.link(ps.get_abs_path(), ps.get_user_rel_ref())

    # TODO: removes ref and file OK but does not remove dir if now empty..
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
            self.storage.remove_ref(ps.get_user_rel_ref())
            self.linker.unlink(ps.get_user_rel_ref())

    def list(self, params=None):
        print "Tracking files:"
        for ref in self.storage.get_index():
            print '~/' + ref

    def status(self, params=None):
        print "{0} repository: {1}".format(config.APP, self.storage.get_repository())

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

        if len(broken_refs) > 0:
            broken_refs.sort(key=lambda tup: tup[1])
            print "Found broken refs:"
            for err_type, reason, ref in broken_refs:
                print "{0}: {1} (type {2})".format(reason, ref, err_type)
            return True
        else:
            print "All OK"

        return False

    def determine_untracked_status(self, ref):
        if ref.startswith('.git/'):
            return None
        if not self.storage.contains_ref(ref):
            return "F", "untracked file", ref
        return None

    def determine_link_status(self, ref):
        R = os.path.join(os.path.expanduser("~"), ref)
        L = os.path.join(self.storage.get_repository(), ref)

        # Case C, E
        if not os.path.exists(L):
            if os.path.exists(R):
                return "C", "ref does not exist in repository but is present in system", ref
            else:
                return "E", "ref does not exist in either repository OR system", ref
        # Case A, B, D (L do exist)
        else:
            # Case D
            if not os.path.exists(R):
                return "D", "new (non existing) upstream ref", ref
            # Case A, B (R do exist)
            else:
                if os.path.samefile(R, L):
                    # L, R points to same inode, link is OK but could still diff from what is in git db
                    if self.git_repo.head.commit.diff(None, paths=ref):
                        return "A", "not committed to version control", ref
                else:
                    return "B", "inode mismatch for ref", ref
        return None

    # diff for cases A, B
    def show(self, params):
        if len(params) != 1:
            log.error("can only handle one ref at a time")
            sys.exit(1)

        ref = params[0]
        log.debug("deteremine show for: " + ref)

        status = self.determine_untracked_status(ref)

        if not status:
            status = self.determine_link_status(ref)

        if status:
            err_type, reason, ref = status

            R = os.path.join(os.path.expanduser("~"), ref)
            L = os.path.join(self.storage.get_repository(), ref)

            if err_type == "A":
                for diff in self.git_repo.head.commit.diff(None, paths=L, create_patch=True):
                    log.info(diff)
            elif err_type == "B":
                self.show_file_diff(L, R)
            elif err_type == "C":
                self.show_file_diff(None, R)
            elif err_type == "D":
                self.show_file_diff(L, None)
            elif err_type == "E":
                log.info(reason)
            elif err_type == "F":
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
        pathspecs = []
        home = os.path.expanduser("~")
        for ref in self.storage.get_index():
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
            self.linker.link(ps.get_abs_path(), ps.get_user_rel_ref())
            if not self.storage.contains_ref(ps.get_user_rel_ref()):
                self.storage.add_ref(ps.get_user_rel_ref())

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
            track_ref_path = ps.get_user_rel_ref()
            track_abs_path = os.path.join(self.storage.get_repository(), track_ref_path)
            if not self.storage.contains_ref(ps.get_user_rel_ref()):
                print "File not tracked (use --add <pathspec> to start tracking): {0}".format(ps.get_abs_path())
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