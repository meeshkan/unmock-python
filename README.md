# [Unmock](https://www.unmock.io/) (Python SDK)
[![CircleCI](https://circleci.com/gh/unmock/unmock-python.svg?style=svg)](https://circleci.com/gh/unmock/unmock-python)

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
    - [Node version support](#node-version-support)
  - [Usage](#usage)
    - [Tests](#tests)
    - [Development](#development)
    - [unmock.io](#unmockio)
    - [Saving mocks](#saving-mocks)
    - [Ignoring aspects of a mock](#ignoring-aspects-of-a-mock)
    - [Adding a signature](#adding-a-signature)
    - [Whitelisting API](#whitelisting-api)
    - [unmock.io tokens](#unmockio-tokens)
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

In your unit tests, you can invoke unmock like this:

```python
import pytest
import requests
import unmock

@pytest.fixture
def unmocker():
    unmock.init()  # Called before the test starts
    yield
    unmock.reset()  # Called after the test ends

def test_behance(unmocker):
    response = requests.get("https://www.behance.net/v2/projects/5456?api_key=u_n_m_o_c_k_200")
    assert response.json().get("project").get("id") == 5456
```

The above syntax uses pytest, but the same is easily accomplishable in
other test suites, even your own custom made one!

Unmock will then either serve JIT semantically functionally correct
mocks from its database or an empty JSON object for unmocked APIs that
can be filled in by the user. The address of these editable objects is
printed to the command line during tests.

### Development

After you create your flask, django, or own server, call


```python
unmock_options = unmock.init()
unmock_options.ignore("story")
```

This has the same effect as activating unmock in your tests.
It will intercept HTTP traffic and serve semantically and functionally
adequate mocks of the APIs in the unmock catalogue.
The main difference is the result of `ignore("story")` passed to unmock
options, which tells the service to ignore the order of mocked requests.
Always use this option when the order of mocked data does not matter,
i.e. when you are in sandbox or development mode.
For users of the [unmock.io](https://www.unmock.io) service, this will
help unmock better organize your mocks in its web dashboard.


### unmock.io

The URLs printed to the command line are hosted by unmock.io. You can
consult the documentation about that service
[here](https://www.unmock.io/docs).

### Saving mocks

All mocks can be saved to a folder called `.unmock` in your user's home
directory by adding a `save` field to the unmock options object like so:

```python
unmock_options = unmock.init(save=True)
```
You can also specify a specific location to save the directory:
```python
unmock_options = unmock.init(save=True, path=".")  # Saves in current path
```
Unmock refers to every mock by a unique hash. Individual mocks or groups
of mocks can be saved by setting save to either a single hash or an
array of hashes like so:

```python
unmock_options = unmock.init(save=["ahash", "anotherhash", "yetanotherhash"])
```

### Ignoring aspects of a mock

Sometimes, you would like for two mocks of slightly API calls to be
treated as equivalent by unmock. For example, you may want all `GET`
calls to the same path with different headers to be served the same
mock. To do this, use the `ignore` field of the unmock options object.
You can do this while initializing unmock or afterwards (as shown before
with ignoring `"story"`):

```python
# Option A:
unmock_options = unmock.init()
unmock_options.ignore("headers", "story")
# Option B:
unmock.init(unmock.UnmockOptions(ignore=["headers", "story"]))
```

The following fields may be ignored:

* `headers`: the headers of the request
* `hostname`: the hostname of the request
* `method`: the method of the request (ie GET, POST, PUT, DELETE).
Note that this is *case insensitive*!
* `path`: the path of the request
* `story`: the story of the request, meaning its order in a series of requests

Ignore evaluates regular expressions, so you can also pass
`"headers|path"` instead of `["headers", "path"]`. Furthermore, to
ignore nested headers, pass a dictionary such as
`{"headers": "Authorization" }`, or to match against the value of a
header, `{"headers": { Authorization: "Bearer *" }}`. When using the
ignore _method_ on the `UnmockOptions` object, you may pass either a
list (`*args`) or a dictionary (`**kwargs`).

### Adding a signature

Sometimes, it is useful to sign a mock with a unique signature. This is
useful, for example, when AB testing code that should serve two
different mocks for the same endpoint in otherwise similar conditions.
To do this, use the `signature` field of the unmock options object:

```python
# Option A:
unmock_options = unmock.init()
unmock_options.signature = "signature-for-this-particular-test"
# Option B
unmock.init(unmock.UnmockOptions(signature="signature-for-this-particular-test"))
```

### Whitelisting API

If you do not want a particular API to be mocked, whitelist it.

```python
# Option A:
unmock_options = unmock.init()
unmock_options.whitelist = ["api.hubspot.com", "api.typeform.com"]
# Option B:
unmock.init(unmock.UnmockOptions(whitelist=["api.hubspot.com", "api.typeform.com"]))
```

### unmock.io tokens

If you are subscribed to the [unmock.io](https://www.unmock.io) service,
you can pass your unmock token directly to the unmock object.

```
unmock.init(token="my-token")
```

At a certain point this becomes a bit tedious, (even if very readable),
at which point you will want to create a credentials file. See
[unmock.io/docs](https://www.unmock.io/docs) for more information on
credential files.
Behind the scenes, we automatically create a credentials file for you,
for caching purposes. With this, subsequent calls to `unmock.init()`
will read the token from the credential files. 

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

