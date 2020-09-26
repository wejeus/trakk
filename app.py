# author: Samuel Wejeus (samuel@isalldigital.com)
import sys
import filecmp
import git
import os

from pathspec import Pathspec
from broken_ref_type import BrokenRefType
from ref_store import RefStore
from linker import Linker
from config import Config, APP
import log

AVAILABLE_ACTIONS = ["list", "status", "sync", "add", "remove", "show"]

# Everything must be initialized (with a config rc file and all before we can use anything in App)
class App:
    def __init__(self, config: Config, ref_store: RefStore, linker: Linker, git_repo: git.Repo):
        self.ref_store = ref_store
        self.linker = linker
        self.git_repo = git_repo

    # remove then add?
    def move(self, src, dest):
        raise Exception("NOT IMPLEMENTED YET!")

    def add_recursive(self, path, resolved) -> bool:
        ps = None
        try:
            ps = Pathspec(path)
        except Exception as e:
            log.error(e)
            return False

        if ps.is_dir_ref():
            entries = os.listdir(ps.get_abs_path()) # get all files and folder in directory
            for subpath in entries:
                print(os.path.join(ps.get_abs_path(), subpath))
                self.add_recursive(os.path.join(ps.get_abs_path(), subpath), resolved)
        else:
            resolved.append(ps)      
        return True
            

    # param could be either a path to a file or directory. Only a single param at a time is currently supported.
    def add(self, params):
        if len(params) == 1:
            param = params[0]
            resolved = []
            if self.add_recursive(param, resolved):
                for ps in resolved:
                    if self.ref_store.contains_ref(ps): # TODO should also check? os.path.isfile(ps.get_abs_path()):
                        log.info("File already tracked: {0}".format(ps))
                        continue
                    self.ref_store.add_ref(ps)  # best to save ref first if something goes wrong later
                    self.linker.link(ps)
                
                maybeDirPathspec = Pathspec(param)
                if maybeDirPathspec.is_dir_ref():
                    self.ref_store.add_dir_ref(maybeDirPathspec)
            else:
                log.error("Could not resolve param")

            # if param is dir: add separate entry in ref_store indicating that it is a directory being tracked
        else:
            log.error("Can only add a single path (file or directory) at a time!")

        # Edge case: what happens when adding a dir and a file in that dir is already tracked?
        
    # can be used to either remove a ref pointed to by path in repo dir
    # or by pointing to original source file. Either way refs are remove
    # and (maybe) unlinked if needed.
    def remove(self, pathspecs: Pathspec):
        log.error("TODO: implement removal of directory")

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
                self.ref_store.remove_ref(ps)
            except Exception as e:
                pass
            self.linker.unlink(ps)

    def list(self, params=None):
        log.info("Tracking files:")
        refs = self.ref_store.get_index()
        if not refs:
            log.info("None")
            return
        for ref in refs:
            log.info('~/' + ref)

    def get_broken_refs(self):
        broken_refs = []
        git_diff_refs = [item.a_path for item in self.git_repo.index.diff(None)] + [item.a_path for item in self.git_repo.index.diff("HEAD")]
        # Handle cases tracked by INDEX
        for ref_name in self.ref_store.get_index():
            status = self.determine_link_status(ref_name)
            if ref_name in git_diff_refs:
                git_diff_refs.remove(ref_name)
            if status:
                broken_refs.append(status)

        # Handle dangling files NOT tracked by index
        repo = self.ref_store.get_repository()
        for root, _, files in os.walk(repo):
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
            broken_refs.append(BrokenRefType.A(mine, theirs))

        return broken_refs

    def status(self, params=None):
        log.error("TODO: implement sync status of folders!")

        broken_refs = self.get_broken_refs()
        if len(broken_refs) > 0:
            # broken_refs.sort(key=lambda tup: tup[1]) throws "instance has no attribute '__getitem__'" since no longer tuple
            log.info("{0} - Found broken or inconsistent refs:".format(APP))
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
            log.info("{0} - All OK".format(APP))
        return False

    # ref param could be either local or from repo. must handle both cases and separate correctly into mine/theirs
    def mine_theirs_from_ref(self, ref):
        mine = os.path.join(os.path.expanduser("~"), ref) # R
        theirs = os.path.join(self.ref_store.get_repository(), ref) # L
        return mine, theirs

    # determines tracked status of a path like name. That is a ref relative <repository>
    def determine_track_status(self, ref_name):
        if ref_name.startswith('.git/'):
            return None
        log.debug("determine track status for: {0}".format(ref_name))
        repo = self.ref_store.get_repository()
        theirs_ps = Pathspec(os.path.join(repo, ref_name))
        if not self.ref_store.contains_ref(theirs_ps):
            return BrokenRefType.F(theirs_ps.get_abs_path())
        return None

    def determine_link_status(self, ref):
        mine, theirs = self.mine_theirs_from_ref(ref)

        # Case C, E
        if not os.path.exists(theirs):
            if os.path.exists(mine):
                return BrokenRefType.C(mine, theirs)
            else:
                return BrokenRefType.E(mine, theirs)
        # Case A, B, D (theirs do exist)
        else:
            # Case D
            if not os.path.exists(mine):
                return BrokenRefType.D(mine, theirs)
            # Case A, B (mine do exist)
            else:
                if os.path.samefile(mine, theirs):
                    # theirs, mine points to same inode, link is OK but could still diff from what is in git db
                    if ref in self.git_repo.untracked_files or self.git_repo.head.commit.diff(None, paths=ref):
                        return BrokenRefType.A(mine, theirs)
                else:
                    return BrokenRefType.B(mine, theirs)
        return None

    # diff for cases A, B
    def show(self, params):
        if len(params) != 1:
            log.error("can only handle one ref at a time")
            sys.exit(1)

        ref = Pathspec.get_ref_from_repo(self.ref_store.get_repository(), Pathspec(params[0]))

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
                # even though inode could be different for 2 files content could be same.
                # We can then auto merge and it does not matter if we use mine or theirs as base
                if filecmp.cmp(broken_ref.mine, broken_ref.theirs):
                    self.linker.link_raw(broken_ref.mine, broken_ref.theirs, True)
                else:
                    self.prompt_choose_ref_to_link(broken_ref.mine, broken_ref.theirs)
            elif broken_ref.type == "C":
                self.prompt_add_ref_to_index(broken_ref.mine)
            elif broken_ref.type == "D":
                self.linker.link_raw(broken_ref.theirs, broken_ref.mine)
            elif broken_ref.type == "E":
                self.prompt_remove_ref_from_index(broken_ref.mine)
            elif broken_ref.type == "F":
                ps = Pathspec(broken_ref.theirs)
                self.ref_store.add_ref(ps)
            elif broken_ref.type == "A":
                # do this last since we only want to commit data when in a clean state
                continue
            else:
                raise Exception("unknown broken ref type: {0}".format(broken_ref))
            # continue rotation of fixing this perticular ref if more actions are needed
            # self.sync_internal([self.determine_link_status(broken_ref.ref)])

    # MARK: - prompt user for input
    
    def prompt_remove_ref_from_index(self, mine):
        ref_name = mine[len(os.path.expanduser("~")):]
        if ref_name.startswith("/"):
            ref_name = ref_name[1:]
        log.info("Ref '{0}' is only present as a name in index (file does not exist in either system or repository). Should I remove it from the index? (Y)es/(S)kip: ".format(ref_name))
        choice = sys.stdin.readline().rstrip().lower()
        if choice == "s":
            return False
        if choice == "y":
            self.ref_store.remove_ref(ref_name, forced=True)
            return True
        else:
            print("What?")
            return self.prompt_remove_ref_from_index(mine)

    def prompt_add_ref_to_index(self, mine):
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
            return self.prompt_add_ref_to_index(mine)

    def prompt_choose_ref_to_link(self, mine, theirs):
        ref = mine
        log.info("Unresolvable file conflict for '{0}' (exists both in system and repository). Which should I pick? (M)ine/(T)heirs/(S)kip: ".format(ref))
        choice = sys.stdin.readline().rstrip().lower()
        if choice == "s":
            return False
        if choice == "m":
            self.linker.link_raw(mine, theirs)
            return True
        if choice == "t":
            self.linker.link_raw(theirs, mine, True)
            return True
        else:
            print("What?")
            return self.prompt_choose_ref_to_link(mine, theirs)



