from .__version__ import __version__  # Conform to PEP-0396

from . import pytest
from .core import UnmockOptions, exceptions

def init(unmock_options=None, story=None, refresh_token=None):
    """Shorthand for initialize"""
    return initialize(unmock_options, story, refresh_token)


def initialize(unmock_options=None, story=None, refresh_token=None):
    """
    Initialize the unmock library for capturing API calls.

    :param unmock_options: An Optional object allowing customization of how unmock works.
    :type unmock_options UnmockOptions
    :param story: An optional list of unmock stories to initialize the state. These represent previous calls to unmock
        and make unmock stateful.
    :type story List[str]
    :param refresh_token: An optional unmock token identifying your account.
    :type refresh_token str
    """

    from . import core  # Imported internally to keep the namespace clear
    if story is not None:
        core.STORIES += story
    if unmock_options is None:  # Default then!
        unmock_options = UnmockOptions(token=refresh_token)

    core.http.initialize(unmock_options)

    return unmock_options


def reset():
    """
    Removes Unmock automatic API call capturing, restoring normal behaviour.
    """
    from . import core
    core.http.reset()