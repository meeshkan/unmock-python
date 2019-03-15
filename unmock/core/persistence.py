from abc import ABCMeta, abstractmethod
import json
import os
from .utils import is_python2
if is_python2():
    import ConfigParser as configparser
else:
    import configparser

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
    def load_auth(self) -> Optional[str]:
        """
        Loads and returns the access token from the persistence layer.
        :return: A string (the access token) if it is found, otherwise None.
        """
        pass

    @abstractmethod
    def load_token(self) -> Optional[str]:
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
        self.homepath = Path(path or Path.home()).absolute()  # Given directory or home path
        self.unmock_dir.mkdir(parents=True, exist_ok=True)  # Create home directory if needed
        # Maps unmock hashes (string) to partial json body (string), when body is read in chunks
        self.partial_body_jsons = dict()

    @property
    def unmock_dir(self):
        return self.homepath.joinpath(".unmock")

    @property
    def token_path(self):
        return self.unmock_dir.joinpath(".token")

    @property
    def config_path(self):
        return self.unmock_dir.joinpath("credentials")

    @property
    def hash_dir(self):
        return self.unmock_dir.joinpath("save")

    def __outdir(self, hash: str) -> Path:
        hashdir = self.hash_dir.joinpath(hash)
        hashdir.mkdir(parents=True, exist_ok=True)
        return hashdir

    def __write_to_hashed(self, hash: str, filename: str, content: Optional[Union[Dict[str, Any], str]]):
        if content is not None:
            with self.__outdir(hash).joinpath(filename).open('w') as fp:
                json.dump(content, fp, indent=2)
                fp.flush()

    def __load_from_hashed(self, hash: str, filename: str) -> Optional[Union[Dict[str, Any], str]]:
        try:
            with self.__outdir(hash).joinpath(filename).open() as fp:
                return json.load(fp)
        except (json.JSONDecodeError, OSError):  # Raise on other errors
            return None

    def save_headers(self, hash: str, headers: Optional[Dict[str, Any]] = None) -> None:
        self.__write_to_hashed(hash=hash, filename=FSPersistence.HEADERS_FILE, content=headers)

    def save_body(self, hash: str, body: Optional[Union[Dict[str, Any], str]] = None) -> None:
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

    def save_auth(self, auth: str) -> None:
        with self.token_path.open('w') as tknfd:
            tknfd.write(auth)
            tknfd.flush()

    def load_headers(self, hash: str) -> Optional[Dict[str, Any]]:
        return self.__load_from_hashed(hash, FSPersistence.HEADERS_FILE)

    def load_body(self, hash: str) -> Optional[Dict[str, Any]]:
        return self.__load_from_hashed(hash, FSPersistence.BODY_FILE)

    def load_auth(self) -> Optional[str]:
        return self.token_path.read_text() if self.token_path.exists() else None

    def load_token(self) -> Optional[str]:
        if self.token is not None:
            return self.token
        if self.config_path.exists():
            iniparser = configparser.ConfigParser()
            iniparser.read(self.config_path)
            return iniparser.get("unmock", "token", fallback=None)
