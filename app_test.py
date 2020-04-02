from pathspec import Pathspec
import os
import pytest
from mockito import when, mock, unstub, ANY
import app

ACTIONS = ["list", "status", "sync", "add", "remove", "show"]

def test_availableActions_shouldContainAllOf():
    trakkApp = app.App(None, None, None, None)
    for action in ACTIONS:
        assert getattr(trakkApp, action, None) != None, "app is missing definition for required action"

def test_availableActions_shouldContainAllOf():
    expected_actions = ACTIONS
    expected_actions.sort()
    available_actions = app.AVAILABLE_ACTIONS
    available_actions.sort()
    assert expected_actions == available_actions, "app is missing declaration of required action"
    