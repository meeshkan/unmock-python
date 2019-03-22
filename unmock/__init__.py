from .__version__ import __version__  # Conform to PEP-0396

from . import pytest
from .core import UnmockOptions, exceptions

def init(**kwargs):
    """Shorthand for initialize"""
    return initialize(**kwargs)


def initialize(**kwargs):
    """
    Initialize the unmock library for capturing API calls.
    Pass keyword arguments to be used for internal options:

    :param save: whether or not to save all mocks (when using boolean value), or a list of specific story IDs to
        save. Deafult to False.
    :type save boolean, list of strings

    :param use_in_production: Whether or not to use unmock in production, based on `ENV` environment variable.
        Default to False.
    :type use_in_production boolean

    :param storage_path: Location where mocks (and credentials, etc) should be stored. Creates a hidden `.unmock`
        directory in that location to store relevant data. Only relevant when saving some of the data.
        Default to None (uses home directory).
    :type storage_path string

    :param logger: A logger file if a user wants to redirect/manage logs in that non-default way. Defaults to a
        console logger, with `info.log` and `debug.log` in a logs directory located in the storage_path.
    :type logger logging.Logger

    :param persistence: A type of persistence layer, can be used to e.g. save mocks automatically to S3 buckets or
        on local disk. Defaults to None and uses file system to store credentials, mocks (if save is defined), etc.
    :type persistence Persistence

    :param ignore: A string, list, dictionary or a combination of them, specifying different parameters to ignore
        when serving mocks. See the documentation for more details.
    :type string, list, dictionary, any

    :param signature: An optional signature allowing a user to have specific mocks for different purposes.
        The signature is used when computing the story hash; see the documentation for more details.
    :type string

    :param refresh_token: An optional refresh token, given when you sign up to the unmock service. With a valid token,
        you can have unlimited calls to the unmock service, an online dashboard, private mocks, etc.
    :type string

    :param whitelist: An optional list (or string) of URLs to whitelist, so that you may access them without unmock
        intercepting the calls. Defaults to ["127.0.0.1", "127.0.0.0", "localhost"]
    :type string, list of strings
    """
    import os
    from . import core  # Imported internally to keep the namespace clear
    new_stories = kwargs.get("story")
    if new_stories is not None:
        core.STORIES += new_stories if isinstance(new_stories, list) else [new_stories]
    # By default, create the .unmock folder under cwd
    kwargs["storage_path"] = kwargs.get("storage_path", os.getcwd())
    unmock_options = UnmockOptions(**kwargs)

    core.http.initialize(unmock_options)

    return unmock_options


def reset():
    """
    Removes Unmock automatic API call capturing, restoring normal behaviour.
    """
    from . import core
    core.http.reset()


def is_mocking():
    """
    Returns whether or not unmock is currently capturing calls
    """
    from . import core
    return len(core.PATCHERS.targets) > 0


class Scope:
    """
    Allows the usage of unmock with scope-specific context managers.
    """
    def __init__(self, **kwargs):
        self.kwargs = kwargs

    def __enter__(self):
        return initialize(**self.kwargs)

    def __exit__(self, exc_type, exc_val, exc_tb):
        reset()
