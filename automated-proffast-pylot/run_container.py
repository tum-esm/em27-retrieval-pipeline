import threading
from src.pylot_factory import PylotFactory
import inspect

def test_thread(factory):
    container_id = container_factory.create_pylot_instance()
    container_factory.execute_pylot(container_id, "a b c", 2)

if __name__ == '__main__':
    container_factory = PylotFactory()
    container_id = container_factory.create_pylot_instance()
    container_factory.execute_pylot(container_id, "a b c", 2)
    x = threading.Thread(target=test_thread, args=(container_factory, ))
    x.start()
    x.join()