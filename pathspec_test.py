import unittest
import pathspec
from os import path

test_env = path.join(path.dirname(path.abspath(__file__)), "test_env")

class PathspecTest(unittest.TestCase):

	def test_CreateRef_FileDoesNotExist_ShouldThrow(self):
		with self.assertRaises(IOError):
			pathspec.Pathspec(test_env)

	def test_CreateRef_RefIsDir_ShouldThrow(self):
		with self.assertRaises(IOError):
			pathspec.Pathspec("~/")

if __name__ == '__main__':
	print("Using test environment: {0}".format(test_env))
	unittest.main()
