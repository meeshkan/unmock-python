import pytest
import unmock as u


@pytest.fixture
def unmock():
  def init(**kwargs):
    u.on(**kwargs)
  yield init
  u.off()
