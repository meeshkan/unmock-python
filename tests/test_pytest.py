import unmock

def test_pytest_local(unmock_local):
    assert unmock.is_mocking()


def test_pytest_local_reinit(unmock_local, tmpdir):
    assert unmock.is_mocking()
    opts = unmock_local(storage_path=tmpdir, save=True)
    assert tmpdir in opts.persistence.hash_dir
    assert unmock.is_mocking()


def test_pytest_local1():
    assert not unmock.is_mocking()  # Not using the unmock_global fixture, unmock has not been called
