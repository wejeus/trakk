import unittest
from mock import Mock
import pathspec



class PathspecTest(unittest.TestCase):

    def test_create(self):
        with self.assertRaises(IOError):
            pathspec.Pathspec("/Users/sawe/git")

#
# if __name__ == '__main__':
#     unittest.main()
