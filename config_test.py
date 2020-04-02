from mockito import when, mock, unstub
from config import Config
import os

def test_readAndWriteRC(tmpdir):
    c = Config()
    when(c).get_rc_file().thenReturn(os.path.join(tmpdir, "dummy-rc-file"))
    c.write_rc("some/repo/path", ["a/ref", "b/ref"])
    repo_path, index = c.read_rc()
    
    assert repo_path == "some/repo/path"
    index.sort()
    assert index == ["a/ref", "b/ref"]
    unstub()

def test_rcName(tmpdir):
    c = Config()
    rc_name = os.path.basename(c.get_rc_file())
    assert rc_name == ".trakk.config"
