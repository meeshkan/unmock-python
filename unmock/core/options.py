from typing import Union, List, Optional

class UnmockOptions:
    def __init__(self, save: Union[bool, List[str]] = False, unmock_host: str = "api.unmock.io", unmock_port = 443,
                 use_in_production: bool = False,
                 logger=None, persistence=None,  # TODO
                 ignore=None, signature: Optional[str] = None, token: Optional[str] = None,
                 whitelist: Optional[List[Str]] = None):
        self.logger = logger
        self.persistence = persistence
        self.save = save
        self.unmock_host = unmock_host
        self.unmock_port = unmock_port
        self.use_in_production = use_in_production
        self.ignore = ignore if ignore is not None else {headers: r"\w*User-Agent\w*"}
        self.signature = signature
        self.token = token
        self.whitelist = whitelist if whitelist is not None else ["127.0.0.1", "127.0.0.0", "localhost"]

"""
export const defaultOptions: IUnmockInternalOptions = {
  ignore: {headers: "\w*User-Agent\w*"},
  logger: isNode ?
    new (__non_webpack_require__("./logger/winston-logger").default)() :
    new (require("./logger/browser-logger").default)(),
  persistence: isNode ?
    new (__non_webpack_require__("./persistence/fs-persistence").default)() :
    new (require("./persistence/local-storage-persistence").default)(),
  save: false,
  unmockHost: "api.unmock.io",
  unmockPort: "443",
  useInProduction: false,
  whitelist: ["127.0.0.1", "127.0.0.0", "localhost"],
};

export interface IUnmockInternalOptions {
    logger: ILogger;
    persistence: IPersistence;
    save: boolean | string[];
    unmockHost: string;
    unmockPort: string;
    useInProduction: boolean;
    ignore?: any;
    signature?: string;
    token?: string;
    whitelist?: string[];
}

export interface IUnmockOptions {
    logger?: ILogger;
    persistence?: IPersistence;
    save?: boolean | string[];
    unmockHost?: string;
    unmockPort?: string;
    ignore?: any;
    signature?: string;
    token?: string;
    whitelist?: string[];
    useInProduction?: boolean;
}
"""
