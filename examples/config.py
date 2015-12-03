# -*- coding: utf-8 -*-

# ...
# Something Server-Config in your project

import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

CHECK_TYPE = 'PRODUCT'

try:
    from local_config import *
except ImportError:
    pass
