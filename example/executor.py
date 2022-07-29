# pyximportx

import cython

# these dependencies are pyximportx dependencies (in principle = user code)
import example.utils.calc
import example.utils.calc_alt as calc_alt
from example.types.container import container


@cython.ccall
def execute():
    cnt0: container = container(10)
    cnt1: container = container(11)
    cnt2: container = container(12)

    calc_res = example.utils.calc.calc0(cnt0, cnt1, cnt2)
    calc_alt_res = calc_alt.calc0(cnt0, cnt1, cnt2)

    calc_res_int: cython.int = calc_res
    calc_alt_res_int: cython.int = calc_alt_res

    print(calc_res_int)
    print(calc_alt_res_int)

if cython.compiled:
    print("executor.py is executed in the compiled mode")
else:
    print("executor.py is executed in the interpreted mode")