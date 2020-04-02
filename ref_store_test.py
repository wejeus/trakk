from pathspec import Pathspec
import os
import pytest
from mockito import when, mock, unstub, verify, verifyZeroInteractions, ANY
from config import Config
from ref_store import RefStore
import logging

LOG = logging.getLogger(__name__)

# Setup/Teardown

@pytest.fixture
def config(initial_index):
    config = mock(Config)
    when(config).read_rc().thenReturn(("", initial_index))
    when(config).write_rc(ANY, ANY)
    yield config
    unstub()

# MARK: - test add

@pytest.mark.parametrize('initial_index', [[]])
def test_addRef_singleRef_addsSingleRef(config):
    ref_store = RefStore(config)
    when(ref_store).check_valid().thenReturn(True)
    
    added = ref_store.add_ref(Pathspec("~/somefile"))

    assert added == True
    assert ref_store.get_index() == ["somefile"]
    verify(config).write_rc("", ["somefile"])

@pytest.mark.parametrize('initial_index', [[]])
def test_addRef_multipleRefs_addsAllRefs(config):
    ref_store = RefStore(config)
    when(ref_store).check_valid().thenReturn(True)

    added = ref_store.add_ref(Pathspec("~/somefile1"))
    added = added and ref_store.add_ref(Pathspec("~/somefile2"))

    assert added == True
    assert ref_store.get_index() == ["somefile1", "somefile2"]
    verify(config, times=2).write_rc(ANY, ANY)

@pytest.mark.parametrize('initial_index', [["somefile"]])
def test_addRef_refAlreadyExists_doNothing(config):
    ref_store = RefStore(config)
    when(ref_store).check_valid().thenReturn(True)
    
    added = ref_store.add_ref(Pathspec("~/somefile"))

    assert added == False
    assert ref_store.get_index() == ["somefile"]
    verify(config, times=0).write_rc(ANY, ANY)

@pytest.mark.parametrize('initial_index', [[]])
def test_addRef_paramNotPathspec_throwException(config):
    ref_store = RefStore(config)
    when(ref_store).check_valid().thenReturn(True)
    with pytest.raises(Exception):
        ref_store.add_ref(4711)

# MARK: - test remove

@pytest.mark.parametrize('initial_index', [["somefile"]])
def test_removeRef_removeSingleExisting_emptyIndex(config):
    ref_store = RefStore(config)
    when(ref_store).check_valid().thenReturn(True)
    
    deleted = ref_store.remove_ref(Pathspec("~/somefile"))

    assert deleted == True
    assert ref_store.get_index() == []
    verify(config).write_rc("", [])

@pytest.mark.parametrize('initial_index', [["somefile1", "somefile2"]])
def test_removeRef_removeSingleExistingWhenMultipleExists_leaveRemainingUnchanged(config):
    ref_store = RefStore(config)
    when(ref_store).check_valid().thenReturn(True)

    deleted = ref_store.remove_ref(Pathspec("~/somefile1"))

    assert deleted == True
    assert ref_store.get_index() == ["somefile2"]
    verify(config).write_rc(ANY, ANY)

@pytest.mark.parametrize('initial_index', [["somefile"]])
def test_removeRef_refNotTracked_doNothing(config):
    ref_store = RefStore(config)
    when(ref_store).check_valid().thenReturn(True)

    deleted = ref_store.remove_ref(Pathspec("~/someuntrackedfile"))

    assert deleted == False
    assert ref_store.get_index() == ["somefile"]
    verify(config, times=0).write_rc(ANY, ANY)

@pytest.mark.parametrize('initial_index', [[]])
def test_removeRef_paramNotPathspec_throwException(config):
    ref_store = RefStore(config)
    when(ref_store).check_valid().thenReturn(True)
    with pytest.raises(Exception):
        ref_store.remove_ref(4711)