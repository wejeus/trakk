from pathspec import Pathspec
import os
import pytest
from mockito import when, mock, unstub, ANY


def test_create():
    path = "somefile"
    when(os.path).expanduser(ANY).thenReturn("/Users/myuser/somefile")
    when(os.path).abspath(ANY).thenReturn("/Users/myuser/somefile")
    try:
        Pathspec(path)
    except IOError:
        pytest.fail("Unexpected: could not create pathspec!")
    unstub()

# MARK: Test ref names

def test_getRef_isFile_returnsRelativePath():
    # (test, expected)
    paths = [("~/someDir/someFile", "someDir/someFile"), ("~/someDir/extraDir/someFile", "someDir/extraDir/someFile")]
    for (testPath, expected) in paths:
        ps = Pathspec(testPath)
        assert ps.get_ref() == expected

def test_getRef_isFileRelativeCurrentDir_returnRelativePath():
    relWorkingDir = os.path.relpath(os.getcwd(), os.path.expanduser("~"))
    paths = [("someDir/someFile", "someDir/someFile"), ("someDir/extraDir/someFile", "someDir/extraDir/someFile")]
    for (testPath, expected) in paths:
        ps = Pathspec(testPath)
        assert ps.get_ref() == relWorkingDir + "/" + expected

def test_getRef_isDir_returnRelativePath():
    # (test, expected)
    when(os.path).isdir(ANY).thenReturn(True)
    paths = [("~", "./"), ("~/dirOnly/", "dirOnly/"), ("~/dirOnly/subDir/", "dirOnly/subDir/")]
    for (testPath, expected) in paths:
        ps = Pathspec(testPath)
        assert ps.get_ref() == expected
    unstub()

def test_getRef_isDirRelativeCurrentDir_returnRelativePath():
    when(os.path).isdir(ANY).thenReturn(True)
    relWorkingDir = os.path.relpath(os.getcwd(), os.path.expanduser("~"))
    paths = [("someDir/", "someDir/"), ("someDir/extraDir/", "someDir/extraDir/")]
    for (testPath, expected) in paths:
        ps = Pathspec(testPath)
        assert ps.get_ref() == relWorkingDir + "/" + expected
    unstub()
        
# MARK: Test ref dirs

def test_getRefDirs_isFile_returnRelativeDirs():
    # (test, expected)
    paths = [("~/someDir/someFile", "someDir"), ("~/someDir/extraDir/someFile", "someDir/extraDir")]
    for (testPath, expected) in paths:
        ps = Pathspec(testPath)
        assert ps.get_ref_dirs() == expected

def test_getRefDirs_isFileRelativeCurrentDir_returnRelativeDirs():
    # (test, expected)
    relWorkingDir = os.path.relpath(os.getcwd(), os.path.expanduser("~"))
    paths = [("someDir/someFile", "someDir"), ("someDir/extraDir/someFile", "someDir/extraDir")]
    for (testPath, expected) in paths:
        ps = Pathspec(testPath)
        assert ps.get_ref_dirs() == relWorkingDir + "/" + expected

def test_getRefDirs_isDir_returnRelativeDirs():
    # (test, expected)
    when(os.path).isdir(ANY).thenReturn(True)
    paths = [("~", "."), ("~/dirOnly/", "dirOnly"), ("~/dirOnly/subDir/", "dirOnly/subDir")]
    for (testPath, expected) in paths:
        ps = Pathspec(testPath)
        assert ps.get_ref_dirs() == expected
    unstub()

def test_getRefDirs_isDirRelativeCurrentDir_returnRelativeDirs():
    when(os.path).isdir(ANY).thenReturn(True)
    relWorkingDir = os.path.relpath(os.getcwd(), os.path.expanduser("~"))
    paths = [("someDir/", "someDir"), ("someDir/extraDir", "someDir/extraDir")]
    for (testPath, expected) in paths:
        ps = Pathspec(testPath)
        assert ps.get_ref_dirs() == relWorkingDir + "/" + expected
    unstub()

# MARK: Test ref in repository

# def test_getRefFromRepo():
#     when(os.path).isdir(ANY).thenReturn(True)
#     relWorkingDir = os.path.relpath(os.getcwd(), os.path.expanduser("~"))
#     paths = [("someDir/", "someDir"), ("someDir/extraDir", "someDir/extraDir")]
#     for (testPath, expected) in paths:
#         ps = Pathspec(testPath)
#         assert ps.get_ref_dirs() == relWorkingDir + "/" + expected
#     unstub()