from mockito import when, mock, unstub
from config import Config
import os

def test_readAndWriteRC(tmpdir):
    c = Config()
    when(c).get_rc_file().thenReturn(os.path.join(tmpdir, "dummy-rc-file"))
    c.write_rc("some/repo/path", ["a/ref", "b/ref"], ["a/dir_ref", "b/dir_ref"])
    repo_path, index, dirs = c.read_rc()
    
    assert repo_path == "some/repo/path"
    index.sort()
    assert index == ["a/ref", "b/ref"]
    dirs.sort()
    assert dirs == ["a/dir_ref", "b/dir_ref"]
    unstub()

def test_rcName(tmpdir):
    c = Config()
    rc_name = os.path.basename(c.get_rc_file())
    assert rc_name == ".trakk.config"
