import pytest
import unmock


@pytest.fixture
def unmock_and_reset():
  def init(**kwargs):
    unmock.on(**default_kwargs)
  yield init
  unmock.off()
