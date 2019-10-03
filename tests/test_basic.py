import unmock
import requests


def replyFn(request):
  if request.host == "www.example.com":
    name = request.qs["name"] or ["World"]
    return {"content": "Hello {}!".format(name[0]), "status": 200}
  return {"status": 400}


def test_reply_fn():
  unmock.on(replyFn=replyFn)
  res = requests.get("http://www.example.com/?name=foo")
  assert res.text == "Hello foo!"
  unmock.off()
