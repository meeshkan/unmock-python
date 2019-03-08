from typing import Dict, Optional
from abc import ABC, abstractmethod
import os

class Persistence(ABC):
    """Defines a high-level interface-like abstract class"""
    def __init__(self, token):
        self.token = token  # Token is only ever saved in memory, everything else is up to the implementation

    @abstractmethod
    def save_headers(self, hash: str, headers: Dict[str, str]) -> None:
        pass

    @abstractmethod
    def save_body(self, hash: str, body: str) -> None:
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
    def load_body(self, hash: str) -> Optional[str]:
        pass

    @abstractmethod
    def load_auth(self) -> Optional[str]:
        pass

    @abstractmethod
    def load_token(self) -> Optional[str]:
        pass


class FSPersistence(Persistence):
    """File system based persistence layer"""
    UNMOCK_DIR = os.path.join(os.path.expanduser("~"), ".unmock")    # Get home directory for current user
    TOKEN_FILE = ".token"
    CONFIG_FILE = "credentials"
    TOKEN_PATH = os.path.join(UNMOCK_DIR, TOKEN_FILE)
    CONFIG_PATH = os.path.join(UNMOCK_DIR, CONFIG_FILE)
    HASH_DIR = os.path.join(UNMOCK_DIR, "save")

    def save_headers(self, hash: str, headers: Dict[str, str]) -> None:
        pass

    def save_body(self, hash: str, body: str) -> None:
        pass

    def save_auth(self, auth: str) -> None:
        pass

    def save_token(self, token: str) -> None:
        pass

    def load_headers(self, hash: str) -> Optional[Dict[str, str]]:
        pass

    def load_body(self, hash: str) -> Optional[str]:
        pass

    def load_auth(self) -> Optional[str]:
        pass

    def load_token(self) -> Optional[str]:
        pass
