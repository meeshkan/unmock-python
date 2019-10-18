# [Unmock](https://www.unmock.io/) (Python SDK)

[![CircleCI](https://circleci.com/gh/unmock/unmock-python.svg?style=shield)](https://circleci.com/gh/unmock/unmock-python)
[![codecov](https://codecov.io/gh/unmock/unmock-python/branch/dev/graph/badge.svg)](https://codecov.io/gh/unmock/unmock-python)
[![PyPI version](https://badge.fury.io/py/unmock.svg)](https://badge.fury.io/py/unmock)

Public API mocking for Python.

Unmock can be used to test modules that perform requests to third-party
APIs like Hubspot, SendGrid, Behance, and hundreds of other public APIs.

Unmock can also be used to mock these APIs in a development environment,
i.e. an express server on a local machine or in a staging environment.

The Unmock Python package offers intuitive, hassle-free SDK to the
Unmock service with minimal setup steps.

The ultimate goal of unmock is to provide a semantically and
functionally adequate mock of the internet.

Unmock also provides access via other languages, all with similar
interface. We have [unmock-js](https://github.com/unmock/unmock-js)
already publicly available, and we are working on .Net, PHP and Java.
We're open to more requests - just [let us know](mailto:contact@unmock.io)!

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

### Quick Start

```python
import unmock
import requests

# Determine the reply callback
def replyFn(request):
  # `request` is a dictionary with keys like `host`, `qs`, etc.
  if request.host == "www.example.com":
    name = request.qs.get("name", ["World"])
    s = "Hello {}!".format(name[0])
    # return value should be a dictionary with keys `content` (body), `status`, and `headers`
    return {"content": s, "status": 200, "headers": {"Content-Length": len(s)}}
  return {"status": 400}

# Activate unmock to start intercepting requests
unmock.on(replyFn=replyFn)
res = requests.get("https://www.example.com/?name=foo")
assert res.text == "Hello foo!"
assert res.headers.get("Content-Length") == str(len("Hello foo!"))
# Disable interception
unmock.off()
```

### Tests

<!-- Write about:
  1. using unmock.on() and possible keywords (replyFn and whitelist)
  1a. unmock.off()
  2. Using with unmock(...)
  3. pytest flag
  4. pytest fixtures
 -->

### Development

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
