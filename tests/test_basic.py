import unmock
import requests


def replyFn(request):
  print(request.__dict__)
  return {"content": "Hello World!", "status": 204, "headers": {"foo?": "bar!"}}


def test_reply_fn():
  unmock.on(replyFn=replyFn)
  res = requests.get("https://www.example.com")
  assert res.text == "Hello World!"
  unmock.off()
