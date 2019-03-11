from typing import Optional, List, Dict, Any, Union
from collections.abs import Iterable
import json

from urllib.parse import urlencode

def json_stringify(obj: Union[List, Dict[Any, Any], Any]):
    if isinstance(obj, Iterable):
        return ''.join(json.dumps(obj if obj is not None and len(obj) > 0 else []))
    return json.dumps(obj)

def build_path(unmock_host: str, xy: bool, story: Optional[List[str]], ignore: Optional[Dict[str, any]],
               headers: Dict[str, Any], host: Optional[str] = None, hostname: Optional[str] = None,
               method: Optional[str] = None, path: Optional[str] = None, signature: Optional[str] = None):
    if hostname == unmock_host or host == unmock_host:
        return path
    unmock_path = "/{xy}/".format(xy="x" if xy else "y")
    qs = {
        "story": json_stringify(story),
        "path": path or "",
        "hostname": hostname or host or "",
        "method": method or "",
        "headers": json_stringify(headers)
    }
    if ignore is not None:
        qs["ignore"] = json_stringify(ignore)
    if signature is not None:
        qs["signature"] = signature
    return "{base}{querystring}".format(base=unmock_path, querystring=urlencode(qs))
