from tests.pylot_test_utils import wrap_test_with_mainlock, run_pylot_test


def test_pylot_1_1(wrap_test_with_mainlock):
    run_pylot_test("pylot_1_1")
