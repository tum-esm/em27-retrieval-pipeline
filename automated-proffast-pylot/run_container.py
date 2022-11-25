import threading
from src.pylot_factory import PylotFactory
import inspect

def test_thread(factory):
    a = container_factory.create_pylot_instance()
    print(inspect.getmodule(a).__file__)

if __name__ == '__main__':
    container_factory = PylotFactory()
    x = threading.Thread(target=test_thread, args=(container_factory, ))
    x.start()
    x.join()