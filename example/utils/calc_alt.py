# pyximportx

import cython

from example.types.container import container

@cython.cfunc
def calc0(cnt0: container, cnt1: container, cnt2: container) -> cython.int:
    return cnt0.multiply_item(cnt1.multiply_item(cnt2.multiply_item(1))) + 10000