from tests.pylot_test_utils import wrap_test_with_mainlock, run_pylot_test


def test_pylot(wrap_test_with_mainlock):
    run_pylot_test()
