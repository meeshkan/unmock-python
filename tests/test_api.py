import unmock
import unmock.core as unmock_core

def test_init_and_reset():
    unmock.init()
    assert len(unmock_core.PATCHERS.targets) == len(unmock_core.PATCHERS.patchers) == 4
    unmock.reset()
    assert len(unmock_core.PATCHERS.targets) == len(unmock_core.PATCHERS.patchers) == 0

    unmock.init(save=True)
    assert len(unmock_core.PATCHERS.targets) == len(unmock_core.PATCHERS.patchers) == 5
    unmock.reset()
    assert len(unmock_core.PATCHERS.targets) == len(unmock_core.PATCHERS.patchers) == 0
