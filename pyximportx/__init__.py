import sys

import pyximportx.cython_patch

from pyximportx.meta_path_finder import meta_path_finder

sys.meta_path.insert(0, meta_path_finder)