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

Unmock works out of the box for most APIs that it mocks and does not
require any additional configuration. For APIs that it does not mock
yet, or to tweak return values from the unmock service, you can consult
the URLs printed to the command line by unmock.

We intend to offer Python2.7 support quite soon, along with other common
libraries such as `aiohttp`, `pycurl`, etc.

## Install

```sh
$ pip install unmock
```

## Usage

### Tests

In your unit tests, you can invoke unmock in several ways:

1. If you're using pytest for your tests, you can either use the unmock
   fixture (you don't even need to import unmock!) -

```python
import pytest
import requests

def test_behance(unmock_local):
    response = requests.get("https://www.behance.net/v2/projects/5456?api_key=u_n_m_o_c_k_200")
    assert response.json().get("project").get("id") == 5456
```

... or you may want to use unmock for all your tests, in which case you
can simply use the `--unmock` flag for pytest:

```bash
pytest tests --unmock
```

2. You can control use unmock in a scoped manner using context managers:

```
# do stuff
with unmock.patch():
    response = requests.get("https://www.example.com/")
# do stuff with mocked response
real_response = requests.get("https://www.example.com/")  # won't be mocked

# You can also access the returned object to modify certain runtime behaviour:
with unmock.patch() as opts:
    # can modify certain behaviour aspects via `opts` object now too
    response = requests.get("https://www.example.com/")
```

3. You can have fine grained control over unmock using the `init` and
   `reset` methods, and modify the `UnmockOptions` object during runtime:

```python
import unmock

# do stuff
opts = unmock.init()
res1 = requests.get("https://www.example.com")  # will be mocked
opts.save = True
res2 = requests.get("https://www.example.com")  # will be mocked and response will be saved
unmock.reset()
res3 = requests.get("https://www.example.com")  # will not be mocked
```

Unmock will then either serve JIT semantically functionally correct
mocks from its database or an empty JSON object for unmocked APIs that
can be filled in by the user. The address of these editable objects is
printed to the command line during tests.

### Development

### unmock.io

The URLs printed to the command line are hosted by unmock.io. You can
consult the documentation about that service
[here](https://www.unmock.io/docs).

## Contributing

Thanks for wanting to contribute! We will soon have a contributing page
detaling how to contribute. Meanwhile, star this repository, open issues
and ask for more features and support!

Please note that this project is released with a
[Contributor Code of Conduct](CODE_OF_CONDUCT.md). By participating in
this project you agree to abide by its terms.

## License

[MIT](LICENSE)

Copyright (c) 2018–2019 [Meeshkan](http://meeshkan.com) and other
[contributors](https://github.com/unmock/unmock/graphs/contributors).
