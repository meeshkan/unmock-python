from typing import Dict, Optional, Union
from abc import ABC, abstractmethod
from pathlib import Path
import json
import configparser

__all__ = ["FSPersistence", "Persistence"]

class Persistence(ABC):
    """Defines a high-level interface-like abstract class"""
    def __init__(self, token):
        self.token = token  # Token is only ever saved in memory, everything else is up to the implementation

    @abstractmethod
    def save_body(self, hash: str, body: Optional[Dict[str, Any]] = None,
                  headers: Optional[Dict[str, Any]] = None) -> None:
        pass

    @abstractmethod
    def save_auth(self, auth: str) -> None:
        pass

    @abstractmethod
    def load_headers(self, hash: str) -> Optional[Dict[str, Any]]:
        pass

    @abstractmethod
    def load_body(self, hash: str) -> Optional[Dict[str, Any]]:
        pass

    @abstractmethod
    def load_auth(self) -> Optional[str]:
        pass

    @abstractmethod
    def load_token(self) -> Optional[str]:
        pass


class FSPersistence(Persistence):
    """File system based persistence layer"""
    HOMEPATH = Path.home()    # Get home directory for current user
    HEADERS_FILE = "response-header.json"
    BODY_FILE = "response.json"

    def __init__(self, token):
        super().__init__(token)
        self.unmock_dir.mkdir(parents=True, exist_ok=True)  # Create home directory if needed

    @property
    def unmock_dir(self):
        return FSPersistence.HOMEPATH.joinpath(".unmock")

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

    def __write_to_hashed(self, hash: str, filename: str, content: Any):
        with self.__outdir(hash).joinpath(filename).open('w') as fp:
            json.dump(content, fp, indent=2)
            fp.flush()

    def __load_from_hashed(self, hash: str, filename: str) -> Optional[Union[Dict[str, Any], str]]:
        try:
            with self.__outdir(hash).joinpath(filename).open() as fp:
                return json.load(fp)
        except (json.JSONDecodeError, OSError):  # Raise on other errors
            return None

    def save_body(self, hash: str, body: Optional[Dict[str, Any]] = None,
                  headers: Optional[Dict[str, Any]] = None) -> None:
        if headers is not None:
            self.__write_to_hashed(hash=hash, filename=FSPersistence.HEADERS_FILE, content=headers)
        if body is not None:
            json_body = "{}"
            try:
                json_body = json.loads(body)
            except json.JSONDecodeError:
                pass
            self.__write_to_hashed(hash=hash, filename=FSPersistence.BODY_FILE, content=json_body)

    def save_auth(self, auth: str) -> None:
        with self.token_path.open('w') as tknfd:
            tknfd.write(auth)
            tknfd.flush()

    def load_headers(self, hash: str) -> Optional[Dict[str, Any]]:
        return self.__load_from_hashed(hash, FSPersistence.HEADERS_FILE)

    def load_body(self, hash: str) -> Optional[Dict[str, Any]]:
        return self.__load_from_hashed(hash, FSPersistence.BODY_FILE)

    def load_auth(self) -> Optional[str]:
        return self.token_path.read_text()

    def load_token(self) -> Optional[str]:
        if self.token is not None:
            return self.token
        if self.config_path.exists():
            iniparser = configparser.ConfigParser()
            iniparser.read(self.config_path)
            return iniparser.get("unmock", "token", fallback=None)
