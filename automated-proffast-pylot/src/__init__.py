import os

proffast_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "prfpylot")

from . import types
from . import utils
from . import procedures
from . import main