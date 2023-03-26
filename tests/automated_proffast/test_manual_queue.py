import pytest
from src import custom_types, interfaces, utils
from ..fixtures import provide_tmp_config, provide_tmp_manual_queue


@pytest.mark.ci
def test_manual_queue(
    provide_tmp_config: custom_types.Config,
    provide_tmp_manual_queue: custom_types.ManualQueue,
) -> None:
    logger = utils.automated_proffast.Logger("testing", print_only=True)

    items = interfaces.automated_proffast.ManualQueueInterface.get_items(logger)
    assert [i.date for i in items] == ["20170103", "20170101", "20170102"]

    interfaces.automated_proffast.ManualQueueInterface.remove_item(
        "so", "20170101", logger
    )
    items = interfaces.automated_proffast.ManualQueueInterface.get_items(logger)
    assert [i.date for i in items] == ["20170103", "20170102"]

    # remove the first item and check get items again
    interfaces.automated_proffast.ManualQueueInterface.remove_item(
        "so", "20170103", logger
    )
    items = interfaces.automated_proffast.ManualQueueInterface.get_items(logger)
    assert [i.date for i in items] == ["20170102"]

    # remove the last item and check get items again
    interfaces.automated_proffast.ManualQueueInterface.remove_item(
        "so", "20170102", logger
    )
    items = interfaces.automated_proffast.ManualQueueInterface.get_items(logger)
    assert [i.date for i in items] == []
