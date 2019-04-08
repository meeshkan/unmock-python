from abc import ABCMeta, abstractmethod
import json
import os
from six.moves import configparser
import yaml
from .utils import makedirs, is_python_version_at_least
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
    def save_metadata(self, hash, data):
        """
        Saves metadata about the original request, client and response.
        :param hash: A story hash
        :type hash string
        :param data: A dictionary of strings as keys and anything serializable as values.
        """
        pass

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

    HEADERS_KEY = "headers"
    DATA_KEY = "body"
    RESPONSE_FILE = "response.json"
    HOMEPATH = os.path.expanduser("~")
    CREDENTIALS_FILE = "credentials"
    METADATA_FILE = "metadata.unmock.yml"

    def __init__(self, token, path=None):
        super(FSPersistence, self).__init__(token)
        self.homepath = os.path.abspath(path or FSPersistence.HOMEPATH)  # Given directory or home path
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
        return os.path.join(self.unmock_dir, FSPersistence.CREDENTIALS_FILE)

    @property
    def hash_dir(self):
        return os.path.join(self.unmock_dir, "save")

    def _outdir(self, hash, *args):
        hashdir = os.path.join(self.hash_dir, hash)
        makedirs(hashdir)
        return os.path.join(hashdir, *args)

    def __write_to_hashed(self, hash, key, content):
        """
        Writes given content to the given filename, to be located in the relevant hash directory
        Returns True upon successful write, False otherwise.
        :param hash: A story hash
        :type hash string
        :param key: The key to use when saving locally
        :type key string
        :param content: An optional serializable content (string or dictionary with string as keys)
        :type dictionary, string
        """
        if content is not None:
            old_contents = self.__load_from_hashed(hash) or dict()
            old_contents[key] = content
            with open(self._outdir(hash, FSPersistence.RESPONSE_FILE), 'w') as fp:
                json.dump(old_contents, fp, indent=2)
                fp.flush()
            return True
        return False

    def __load_from_hashed(self, hash, key=None):
        """
        Attempts to load content from the filename located as the hash directory
        :param hash: A story hash
        :type hash string
        :param key: The key to read from
        :type key string
        :return: The decoded content from filename if successful, None otherwise
        """
        try:
            with open(self._outdir(hash, FSPersistence.RESPONSE_FILE)) as fp:
                cached = json.load(fp)
                if key is None:
                    return cached
                return cached.get(key)
        except (json.JSONDecodeError, OSError, IOError):
            # JSONDecoder when it fails decoding content
            # OSError is for when the file is not found on Python3
            # IOError for when file is not found on Python2
            # Raise on other errors
            return None

    def save_headers(self, hash, headers=None):
        self.__write_to_hashed(hash=hash, key=FSPersistence.HEADERS_KEY, content=headers)

    def save_metadata(self, hash, data):
        if data is None:  # nothing or nowhere to write
            return
        target = self._outdir(hash, FSPersistence.METADATA_FILE)
        content = dict()
        if os.path.exists(target):
            with open(target) as mtdfd:
                content = yaml.safe_load(mtdfd)
        content.update(data)
        with open(target, 'w') as mtdfd:
            yaml.safe_dump(content, mtdfd)

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
        return self.__write_to_hashed(hash=hash, key=FSPersistence.DATA_KEY, content=body)

    def save_auth(self, auth):
        with open(self.token_path, 'w') as tknfd:
            tknfd.write(auth)
            tknfd.flush()

    def load_headers(self, hash):
        return self.__load_from_hashed(hash, FSPersistence.HEADERS_KEY)

    def load_body(self, hash):
        return self.__load_from_hashed(hash, FSPersistence.DATA_KEY)

    def load_auth(self):
        if os.path.exists(self.token_path):
            with open(self.token_path) as tknfd:
                return tknfd.read()
        return None

    def load_token(self):
        if self.token is not None:
            return self.token
        # We check in both the given config_path (default is under cwd) and under user home path.
        # At worse, we check twice if the credentials file exists under the user's homepath.
        for config_file in [self.config_path, os.path.join(FSPersistence.HOMEPATH, FSPersistence.CREDENTIALS_FILE)]:
            if os.path.exists(config_file):
                iniparser = configparser.ConfigParser(defaults={"token": None}, allow_no_value=True)
                iniparser.read(config_file)
                return iniparser.get("unmock", "token")
