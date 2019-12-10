# [Unmock](https://www.unmock.io/) (Python SDK)

[![CircleCI](https://circleci.com/gh/unmock/unmock-python.svg?style=shield)](https://circleci.com/gh/unmock/unmock-python)
[![codecov](https://codecov.io/gh/unmock/unmock-python/branch/dev/graph/badge.svg)](https://codecov.io/gh/unmock/unmock-python)
[![PyPI version](https://badge.fury.io/py/unmock.svg)](https://badge.fury.io/py/unmock)
[![Chat on Gitter](https://badges.gitter.im/gitterHQ/gitter.png)](https://gitter.im/unmock/community)

Public API mocking for Python.

Unmock can be used to test modules that perform requests to third-party
APIs like Hubspot, SendGrid, Behance, and hundreds of other public APIs.

Unmock can also be used to mock these APIs in a development environment,
i.e. an express server on a local machine or in a staging environment.

The Unmock Python package offers a minimal, "do-it-yourself" SDK to mock responses with minimal intrusion to your codebase.

The ultimate goal of unmock is to provide a semantically and
functionally adequate mock of the internet.

Unmock also provides access via other languages. Our most advanced and up-to-date package is [unmock-js](https://github.com/unmock/unmock-js) - check it out to see what's coming soon to Python!
Unmock for .Net, PHP and Java is in the works. We're open to more requests - just [let us know](mailto:contact@unmock.io)!

**Table of Contents**

<!-- toc -->

- [Unmock](#unmock)
  - [How does it work?](#how-does-it-work)
  - [Install](#install)
  - [Usage](#usage)
    - [Tests](#tests)
    - [Development](#development)
    - [unmock.io](#unmockio)
  - [Contributing](#contributing)
  - [License](#license)

<!-- tocstop -->

## How does it work?

Unmock works by overriding Python's low-level `HTTPConnection`'s and
`HTTPRequest`'s functions, thereby capturing calls
made by popular packages such as `requests` and `urllib3`.

## Install

```sh
$ pip install unmock
```

## Usage

### Capturing outgoing requests

There are many ways to import unmock and start using it. You may choose from the following methods, as per fits your needs:

```python
""" 1: verbose: """
# test_foo.py
import unmock
# ...
unmock.on()
# do stuff with outgoing requests
unmock.off()

""" 2: context manager """
# test_foo.py
import unmock
with unmock.patch():
  # do stuff with outgoing requests

""" 3: with as a pytest plugin: """
# test_foo.py
# run with `pytest --unmock`
def test_my_awesome_function(unmock):
  # do stuff with outgoing requests
```

### Ingesting responses

The above snippets will capture all outgoing requests, and return an empty body response with status code 200 (`OK`) for all requests.  
Of course - that's not what we set out to do. Behind the scenes, unmock aggregates the outgoing information until the request is ready to be sent, and it then sends out a `Request` object with the following interface:

```python
Request.host:     str  # The hostname, e.g. `www.example.com`
Request.endpoint: str  # The endpoint requested, may include a query string, e.g. `/`, or `/foo/?bar=baz`
Request.method:   str  # The HTTP method requested, e.g. `GET`
Request.port:     int  # The port used in the request. This effectively represents HTTP (80), HTTPS (443), or custom port
Request.headers:  Dict[str, str]  # A mapping of headers and their values
Request.data:     Union[None, Any]  # The body of the request, if any
Request.qs:       Dict[str, List[str]]  # A mapping of query string and the values associated with them
```

### Specifying responses

The `Request` class allows you to filter requests and reply with different responses, based on the request data. A typical response is a **dictionary** consisting of up to 3 items:

- `"content"`: a string or a dictionary (JSON-parsable) for the content of the response. Defaults to the empty string if not specified.
- `"status"`: an integer specifying the HTTP status code response. Defaults to 200 (`OK`) if not specified.
- `"headers"`: a mapping between a header and its value. Defaults to an empty dictionary if not specified.

### Tying it together (and other keyword arguments)

`unmock.on()`, `unmock.patch()` and the `unmock` fixture in pytest can be called with two keyword arguments. The first and most important one is `replyFn`. It accepts a function which will be used to generate responses. The `replyFn` will be called every time a request is made, and will be passed the single `Request` class as defined above. The returned value is expected to be a dictionary matching the response dictionary.  
Additionally, one may specify a list of whitelisted hosts/endpoints, for which the request will be allowed to pass through, using the `whitelist` keyword argument. An asterisk is used as a wildcard if you wish to capture an entire hostname (e.g. `*.google.com/*` will capture any and all requests made to Google).

### Examples

The following example snippet uses the `unmock` fixture (with pytest). The `replyFn` returns either a 200 response for requests to `zodiac.com` or 404 for any other website. For zodiac-requests, it returns a mock for requests to the scorpio horoscope, otherwise it returns an empty response.

```python
# horoscope.py
import requests
def get_horoscope(sign):
  return requests.get("https://zodiac.com/horoscope/{}".format(sign))

# test_horoscope.py
from horoscope import get_horoscope

def replyFn(req):
  if "zodiac.com" in req.host:
    sign = req.endpoint.split("/")[-1]
    if sign.lower() == "scorpio":
      return {"content": {"horoscope": "You will be lucky! Someday..."}, "status": 200 }
    return {"status": 200}
  return {"status": 404}

def test_horoscope(unmock):
  unmock(replyFn=replyFn)
  res = get_horoscope("scorpio")
  assert res.status_code == 200
  assert res.json().get("horoscope") == "You will be lucky! Someday..."
```

### unmock.io

The URLs printed to the command line are hosted by unmock.io. You can
consult the documentation about that service
[here](https://www.unmock.io/docs).

## Contributing

Thanks for wanting to contribute! We will soon have a contributing page
detaling how to contribute. Meanwhile, feel free to star this repository, open issues
and ask for more features and support.

Please note that this project is governed by the [Unmock Community Code of Conduct](https://github.com/unmock/code-of-conduct). By participating in this project, you agree to abide by its terms.

## License

[MIT](LICENSE)

Copyright (c) 2018–2019 [Meeshkan](http://meeshkan.com) and other
[contributors](https://github.com/unmock/unmock/graphs/contributors).
