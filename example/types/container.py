# pyximportx

import cython

@cython.cclass
class container:
    item: cython.int

    def __init__(self, item: cython.int):
        self.item = item * 1

    @cython.ccall
    def multiply_item(self, n: cython.int) -> cython.int:
        return self.item * n