import unmock
import requests


def replyFn(request):
  if request.host == "www.example.com":
    name = request.qs["name"] or ["World"]
    s = "Hello {}!".format(name[0])
    return {"content": s, "status": 200, "headers": {"Content-Length": len(s)}}
  return {"status": 400}


def test_reply_fn():
  unmock.on(replyFn=replyFn)
  res = requests.get("https://www.example.com/?name=foo")
  assert res.text == "Hello foo!"
  unmock.off()


def test_context_manager():
  with unmock.patch(replyFn=replyFn):
    res = requests.get("https://www.example.com/?name=bar")
    assert res.text == "Hello bar!"


def test_pytest_fixture(unmock_t):
  unmock_t(replyFn=replyFn)
  res = requests.get("https://www.example.com/?name=baz")
  assert res.text == "Hello baz!"
