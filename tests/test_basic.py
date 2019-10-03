import unmock
import requests


def replyFn(request):
  if request.host == "www.example.com":
    name = request.qs["name"] or ["World"]
    return {"content": "Hello {}!".format(name[0]), "status": 200}
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


def test_pytest_fixture(unmock):
  unmock(replyFn=replyFn)
  res = requests.get("https://www.example.com/?name=baz")
  assert res.text == "Hello baz!"
