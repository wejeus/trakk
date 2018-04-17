import unittest
import pathspec
from os import path, remove, removedirs, system
import config
from subprocess import call
from contextlib import suppress

test_env = path.join(path.dirname(path.abspath(__file__)), "test_env")
trakk_bin = path.join(path.dirname(path.abspath(__file__)), "trakk.py")
trakk_rc = path.join(path.expanduser("~"), config.__TRAKK_CONFIG_FILENAME)
repo_path = path.join(test_env, "repo")

def cleanEnv():
	# with suppress(Exception): remove(trakk_rc)
	with suppress(Exception): removedirs(repo_path)

	# try: remove(trakk_rc) except: pass
	# try: removedirs(path) except: pass
	
		# exception if file dont exists, which is fine

class PathspecTest(unittest.TestCase):

	def test_Init_CleanEnvironment_ShouldSucceed(self):
		cleanEnv()
		# system("{0} --init {1}".format(trakk_bin, repo_path))
		# self.assertTrue(path.isfile(trakk_rc))

if __name__ == '__main__':
	print("Using test environment: {0}".format(test_env))
	unittest.main()
