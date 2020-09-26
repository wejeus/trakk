import os
import json
import log

APP = "Trakk"
VERSION = 0.5

_TRAKK_CONFIG_FILENAME = '.trakk.config'

_JSON_KEY_REPOSITORY = 'repository'
_JSON_KEY_REFS = 'refs' # the index
_JSON_KEY_DIRS = 'dirs' # the index of tracked dirs


# returns a path to existing repository if exists and current index
class Config:

    # run-configuration file
    def get_rc_file(self): 
        return os.path.join(os.path.expanduser("~"), _TRAKK_CONFIG_FILENAME)

    def read_rc(self):
        rc = self.get_rc_file()
        log.debug("reading configuration from: " + rc)
        if not os.path.isfile(rc):
            return None, []

        data = None
        with open(rc, 'r') as f:
            data = json.loads(f.read())

        if _JSON_KEY_REPOSITORY in data:
            repo_path = data[_JSON_KEY_REPOSITORY]
        else:
            repo_path = None
        
        if _JSON_KEY_REFS in data:
            index = data[_JSON_KEY_REFS]
        else:
            index = []

        if _JSON_KEY_DIRS in data:
            dirs = data[_JSON_KEY_DIRS]
        else:
            dirs = []

        log.debug("read repository path: " + repo_path)
        return repo_path, index, dirs

    # Writes a config file with pointer to repository. Assumes repository path have been verified for correctness
    def write_rc(self, repo_path: str, index: [str], dirs: [str]):
        data = {_JSON_KEY_REPOSITORY: repo_path, _JSON_KEY_REFS: index, _JSON_KEY_DIRS: dirs}
        encoded = json.dumps(data)
        rc = self.get_rc_file()
        log.debug("writing configuration to: " + rc + " with repository path: " + repo_path)
        with open(rc, 'w') as f:
            f.write(encoded)

