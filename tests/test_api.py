import unmock
import unmock.core as unmock_core

def assert_number_of_patches(expected_number):
    assert len(unmock_core.PATCHERS.targets) == len(unmock_core.PATCHERS.patchers) == expected_number

def test_init_and_reset():
    unmock.init()
    assert_number_of_patches(4)  # Four different function for HTTPRequest
    unmock.reset()
    assert_number_of_patches(0)

    unmock.init(save=True)
    assert_number_of_patches(5)  # Plus one for HTTPResponse
    unmock.reset()
    assert_number_of_patches(0)

def test_context_manager():
    assert_number_of_patches(0)
    with unmock.Scope():
        assert_number_of_patches(4)
    assert_number_of_patches(0)
    with unmock.Scope(save=True):
        assert_number_of_patches(5)
    assert_number_of_patches(0)
