from typing import Dict, Optional, Union
from abc import ABC, abstractmethod
from pathlib import Path
import json
import configparser

__all__ = ["FSPersistence"]

class Persistence(ABC):
    """Defines a high-level interface-like abstract class"""
    def __init__(self, token):
        self.token = token  # Token is only ever saved in memory, everything else is up to the implementation

    @abstractmethod
    def save_body(self, hash: str, body: str = None, headers: str = None) -> None:
        pass

    @abstractmethod
    def save_auth(self, auth: str) -> None:
        pass

    @abstractmethod
    def save_token(self, token: str) -> None:
        pass

    @abstractmethod
    def load_headers(self, hash: str) -> Optional[Dict[str, str]]:
        pass

    @abstractmethod
    def load_body(self, hash: str) -> Optional[Dict[str, str]]:
        pass

    @abstractmethod
    def load_auth(self) -> Optional[str]:
        pass

    @abstractmethod
    def load_token(self) -> Optional[str]:
        pass


class FSPersistence(Persistence):
    """File system based persistence layer"""
    UNMOCK_DIR = Path.home().joinpath(".unmock")    # Get home directory for current user
    TOKEN_PATH = UNMOCK_DIR.joinpath(".token")
    CONFIG_PATH = UNMOCK_DIR.joinpath("credentials")
    HASH_DIR = UNMOCK_DIR.joinpath("save")
    HEADERS_FILE = "response-header.json"
    BODY_FILE = "response.json"

    def __init__(self, token):
        super().__init__(token)
        FSPersistence.UNMOCK_DIR.mkdir(parents=True, exist_ok=True)  # Create home directory if needed

    @staticmethod
    def __outdir(hash: str):
        hashdir = FSPersistence.HASH_DIR.joinpath(hash)
        hashdir.mkdir(parents=True, exist_ok=True)
        return hashdir

    @staticmethod
    def __write_to_hashed(hash: str, filename: str, content: str):
        with FSPersistence.__outdir(hash).joinpath(filename).open('w') as fp:
            json.dump(content, fp, indent=2)
            fp.flush()

    @staticmethod
    def __load_from_hashed(hash: str, filename: str) -> Optional[Union[Dict[str, str], str]]:
        try:
            with FSPersistence.__outdir(hash).joinpath(filename).open() as fp:
                return json.load(fp)
        except (json.JSONDecodeError, OSError):  # Raise on other errors
            return None

    def save_body(self, hash: str, body: str = None, headers: str = None) -> None:
        if headers is not None:
            FSPersistence.__write_to_hashed(hash=hash, filename=FSPersistence.HEADERS_FILE, content=headers)
        if body is not None:
            json_body = "{}"
            try:
                json_body = json.loads(body)
            except json.JSONDecodeError:
                pass
            FSPersistence.__write_to_hashed(hash=hash, filename=FSPersistence.BODY_FILE, content=json_body)

    def save_auth(self, auth: str) -> None:
        with FSPersistence.TOKEN_PATH.open('w') as tknfd:
            tknfd.write(auth)
            tknfd.flush()

    def load_headers(self, hash: str) -> Optional[Dict[str, str]]:
        return FSPersistence.__load_from_hashed(hash, FSPersistence.HEADERS_FILE)

    def load_body(self, hash: str) -> Optional[Dict[str, str]]:
        return FSPersistence.__load_from_hashed(hash, FSPersistence.BODY_FILE)

    def load_auth(self) -> Optional[str]:
        return FSPersistence.TOKEN_PATH.read_text()

    def load_token(self) -> Optional[str]:
        if self.token is not None:
            return self.token
        if FSPersistence.CONFIG_PATH.exists():
            iniparser = configparser.ConfigParser()
            iniparser.read(FSPersistence.CONFIG_PATH)
            return iniparser.get("unmock", "token", fallback=None)
