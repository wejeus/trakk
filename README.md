TRAC - Simple tracking and backup system

# What

* Hard linking of dirs not possible. Must handle translation to which files self
* Use pythons since its likely installed on system and have no dependencies. Only dependency is git
* Assumption: base dir is always: ~/
* If new tracked entry masks previous entry remove previous and use more general entry

Trakk
## Usage

track --add <pathspec>
* resolves to path relative home dir (~/[file|dir])
* creates hard link to given pathspec: <configured_repo>/[file|dir]
* add entry to ~/.track.config list of tracked files

track --remove [file|dir]
* remove [file|dir] from being tracked (does not remove from git history):
* remove entry from list in ~/.track.config
* remove hard link from repository dir

track --version
* TODO

track --resolve
* TODO

track --clone <git repository>
* TODO
* checkout repository and init track

track --init ~/system
* TODO
* creates ~/.track.config config file with pointer to ~/system
* initialized list of tracked files from ~/system/.track if exists or empty list

track --status
* TODO
* checks that list of entries in ~/.track.config is in sync with repository dir

track --restore 
* TODO
* copies all (non symlinked since broken) content of ~/system to ~/
* setup new links

track --sync
* TODO


# ROADMAP
* Move ref database into repo dir. Should be transparent to normal git usage and updated and commited automatically (potential updates to origin will be detected by git)
* add & remove to and from Storage should also add/remove to git repo
* When initializing new dir automatically create directory structure instead of require that it already exists