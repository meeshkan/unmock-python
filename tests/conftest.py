import pytest
import unmock as u


@pytest.fixture
def unmock_t():  # Defined internally for test suites
  def init(**kwargs):
    u.off()
    u.on(**kwargs)
  u.on()
  yield init
  u.off()
