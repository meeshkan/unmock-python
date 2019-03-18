from abc import ABCMeta, abstractmethod
import json
import os
from .utils import makedirs, is_python_version_at_least
from six.moves import configparser
if not is_python_version_at_least("3.5"):
    json.JSONDecodeError = ValueError  # JSONDecodeError was introduced in Python3.5, before it would throw ValueError


__all__ = ["FSPersistence", "Persistence"]

class Persistence:
    """Defines a high-level interface-like abstract class"""
    __metaclass__ = ABCMeta
    def __init__(self, token):
        """
        Initializes the persistence layer.
        :param token: A refresh token to be used
        :type token string
        """
        self.token = token  # Token is only ever saved in memory, everything else is up to the implementation

    @abstractmethod
    def save_headers(self, hash, headers=None):
        """
        Saves given headers in the persistence layer.
        :param hash: A story hash
        :type hash string
        :param headers: A dictionary of strings as keys and anything serializable as values. Default is None.
        """
        pass

    @abstractmethod
    def save_body(self, hash, body=None):
        """
        Saves the given body in the persistence layer.
        :param hash: A story hash
        :type hash string
        :param body: A string or a dictionary of strings as keys and anything serializable as values. Default is None.
        """
        pass

    @abstractmethod
    def save_auth(self, auth):
        """
        Saves an access token in the persistence layer.
        :param auth: Access token
        :type auth string
        """
        pass

    @abstractmethod
    def load_headers(self, hash):
        """
        Loads the headers for the matching story hash and returns them.
        :param hash: A story hash
        :type hash string
        :return: A dictionary with strings as keys and anything serializable as values.
            None if story hash can't be found or headers could not be loaded.
        """
        pass

    @abstractmethod
    def load_body(self, hash):
        """
        Loads the body for the matching story hash and returns it.
        :param hash: A story hash
        :type hash string
        :return: A dictionary with strings as keys and anything serializable as values.
            None if story hash can't be found or body could not be loaded.
        """
        pass

    @abstractmethod
    def load_auth(self):
        """
        Loads and returns the access token from the persistence layer.
        :return: A string (the access token) if it is found, otherwise None.
        """
        pass

    @abstractmethod
    def load_token(self):
        """
        Loads and returns the refresh token from the persistence layer.
        :return: A string (the refresh token) if it was given when initializing the persistence layer, otherwise None.
        """
        pass


class FSPersistence(Persistence):
    """File system based persistence layer"""
    HEADERS_FILE = "response-header.json"
    BODY_FILE = "response.json"

    def __init__(self, token, path=None):
        super(FSPersistence, self).__init__(token)
        self.homepath = os.path.abspath(path or os.path.expanduser("~"))  # Given directory or home path
        makedirs(self.unmock_dir)  # Create home directory if needed
        # Maps unmock hashes (string) to partial json body (string), when body is read in chunks
        self.partial_body_jsons = dict()

    @property
    def unmock_dir(self):
        return os.path.join(self.homepath, ".unmock")

    @property
    def token_path(self):
        return os.path.join(self.unmock_dir, ".token")

    @property
    def config_path(self):
        return os.path.join(self.unmock_dir, "credentials")

    @property
    def hash_dir(self):
        return os.path.join(self.unmock_dir, "save")

    def __outdir(self, hash):
        hashdir = os.path.join(self.hash_dir, hash)
        makedirs(hashdir)
        return hashdir

    def __write_to_hashed(self, hash, filename, content):
        """
        Writes given content to the given filename, to be located in the relevant hash directory
        :param hash: A story hash
        :type hash string
        :param filename: The filename to use when saving
        :type filename string
        :param content: An optional serializable content (string or dictionary with string as keys)
        :type dictionary, string
        """
        if content is not None:
            with open(os.path.join(self.__outdir(hash), filename), 'w') as fp:
                json.dump(content, fp, indent=2)
                fp.flush()

    def __load_from_hashed(self, hash, filename):
        """
        Attempts to load content from the filename located as the hash directory
        :param hash: A story hash
        :type hash string
        :param filename: The filename to read from
        :type filename string
        :return: The decoded content from filename if successful, None otherwise
        """
        try:
            with open(os.path.join(self.__outdir(hash), filename)) as fp:
                return json.load(fp)
        except (json.JSONDecodeError, OSError, IOError):
            # JSONDecode when it fails decoding content
            # OSError is for when the file is not found on Python3
            # IOError for when file is not found on Python2
            # Raise on other errors
            return None

    def save_headers(self, hash, headers=None):
        self.__write_to_hashed(hash=hash, filename=FSPersistence.HEADERS_FILE, content=headers)

    def save_body(self, hash, body=None):
        if isinstance(body, str):
            # Attempt to load back from JSON string to object for dumping to file
            # If unsuccessful, save it as a partial result
            if hash in self.partial_body_jsons:  # Already have a relevant partial
                self.partial_body_jsons[hash] += body
            else:  # Add to a new partial (possibly deleted immediately afterwards)
                self.partial_body_jsons[hash] = body
            try:
                body = json.loads(self.partial_body_jsons[hash])
                del self.partial_body_jsons[hash]  # Success! Remove the partial's cache
            except json.JSONDecodeError:
                body = None  # Failed! Don't access disk just yet...
        self.__write_to_hashed(hash=hash, filename=FSPersistence.BODY_FILE, content=body)

    def save_auth(self, auth):
        with open(self.token_path, 'w') as tknfd:
            tknfd.write(auth)
            tknfd.flush()

    def load_headers(self, hash):
        return self.__load_from_hashed(hash, FSPersistence.HEADERS_FILE)

    def load_body(self, hash):
        return self.__load_from_hashed(hash, FSPersistence.BODY_FILE)

    def load_auth(self):
        if os.path.exists(self.token_path):
            with open(self.token_path) as tknfd:
                return tknfd.read()
        return None

    def load_token(self):
        if self.token is not None:
            return self.token
        if os.path.exists(self.config_path):
            iniparser = configparser.ConfigParser(defaults={"token": None}, allow_no_value=True)
            iniparser.read(self.config_path)
            return iniparser.get("unmock", "token")
