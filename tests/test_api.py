import unmock
import unmock.core as unmock_core


def assert_number_of_patches(expected_number):
  assert len(unmock_core.PATCHERS.targets) == len(
      unmock_core.PATCHERS.patchers) == expected_number


def test_init_and_reset():
  unmock.init()
  assert_number_of_patches(3)  # Three different mocks for HTTPRequest
  unmock.off()
  assert_number_of_patches(0)


def test_context_manager():
  assert_number_of_patches(0)
  with unmock.patch():
    assert_number_of_patches(3)
  assert_number_of_patches(0)
