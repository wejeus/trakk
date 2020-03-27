import os

APP = "Trakk"
VERSION = 0.3

__TRAKK_CONFIG_FILENAME = '.trakk.config'

# run-configuration file
def rc():
	return os.path.join(os.path.expanduser("~"), __TRAKK_CONFIG_FILENAME)
