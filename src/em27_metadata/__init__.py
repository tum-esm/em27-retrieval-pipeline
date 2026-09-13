"""The EM27 Metadata package provides a set of schemas and interfaces for
working with EM27 metadata. It used to be hosted in its own repository at
https://github.com/tum-esm/em27-metadata but is now included in this EM27
Retrieval Pipeline repository since the pipeline is the main consumer of it."""

from . import types as types
from .interfaces import EM27MetadataInterface as EM27MetadataInterface
from .loader import load_from_example_data as load_from_example_data
from .loader import load_from_github as load_from_github
from .loader import load_from_local_files as load_from_local_files
