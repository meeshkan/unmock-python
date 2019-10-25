import unmock
import requests


def replyFn(request):
  print(request)
  if request.host == "www.foo.com":
    name = request.qs.get("name", ["World"])
    s = "Hello {}!".format(name[0])
    return {"content": s, "status": 200, "headers": {"Content-Length": len(s)}}
  return {"status": 200}


def test_reply_fn():
  unmock.on(replyFn=replyFn)
  res = requests.get("https://www.foo.com/?name=foo")
  assert res.text == "Hello foo!"
  assert res.headers.get("Content-Length") == str(len("Hello foo!"))
  unmock.off()


def test_context_manager():
  with unmock.patch(replyFn=replyFn):
    res = requests.get("https://www.foo.com/")
    assert res.text == "Hello World!"
    assert res.headers.get("Content-Length") == str(len("Hello World!"))


def test_pytest_fixture(unmock_t):
  unmock_t(replyFn=replyFn)
  res = requests.get("https://www.foo.com/?name=baz")
  assert res.text == "Hello baz!"
  assert res.headers.get("Content-Length") == str(len("Hello baz!"))
