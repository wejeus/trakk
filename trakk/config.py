import os

APP = "Trakk"
VERSION = 0.3

__TRAKK_CONFIG_FILENAME = '.trakk.config'
# __INDEX_FILENAME = '.trakk-index.config'

# run-configuration file
def rc():
	return os.path.join(os.path.expanduser("~"), __TRAKK_CONFIG_FILENAME)

# def index(abs_repo_path):
# 	return os.path.join(abs_repo_path, __INDEX_FILENAME)

# def index_filename():
# 	return __INDEX_FILENAME