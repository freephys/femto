
import timeit
import numpy as np
import femto as ss

__all__ = ['bench_axis0', 'bench_axis1', 'bench_overhead', 'bench',
           'bench_3d', 'bench_detailed']


def bench_axis0(functions=None):
    "Benchmark performance along axis 0"
    bench(shapes=[(1000, 1000), (1000, 1000), (1000, 1000), (1000, 1000)],
          dtypes=['float64', 'float32', 'int64', 'int32'],
          axes=[0, 0, 0, 0], functions=functions)


def bench_axis1(functions=None):
    "Benchmark performance along axis 1"
    bench(shapes=[(1000, 1000), (1000, 1000), (1000, 1000), (1000, 1000)],
          dtypes=['float64', 'float32', 'int64', 'int32'],
          axes=[1, 1, 1, 1], functions=functions)


def bench_overhead(functions=None):
    "Benchmark performance with small input arrays"
    bench(shapes=[(10, 10), (10, 10), (100, 100), (100, 100)],
          dtypes=['float64', 'float64', 'float64', 'float64'],
          axes=[0, 1, 0, 1], functions=functions)


def bench_3d(shapes=[(100, 100, 100), (100, 100, 100), (100, 100, 100)],
             dtypes=['float64', 'float64', 'float64'],
             axes=[0, 1, 2], order='C', functions=None):
    "Benchmark performance with 3d input arrays"
    bench(shapes, dtypes, axes, order, functions)


def bench(shapes=[(1, 1000), (1000, 1000), (1000, 1000), (1000, 1000),
                  (1000, 1000)],
          dtypes=['float64', 'float64', 'int64', 'float64', 'int64'],
          axes=[1, 0, 0, 1, 1],
          order='C',
          functions=None):
    """
    femto benchmark.

    Parameters
    ----------
    shapes : list, optional
        A list of tuple shapes of input arrays to use in the benchmark.
    dtypes : list, optional
        A list of data type strings such as ['float64', 'int64'].
    axes : list, optional
        List of axes along which to perform the calculations that are being
        benchmarked.
    order : {'C', 'F'}, optional
        Whether to store multidimensional data in C- or Fortran-contiguous
        (row- or column-wise) order in memory.
    functions : {list, None}, optional
        A list of strings specifying which functions to include in the
        benchmark. By default (None) all functions are included in the
        benchmark.

    Returns
    -------
    A benchmark report is printed to stdout.

    """

    if len(shapes) != len(axes):
        raise ValueError("`shapes` and `axes` must have the same length")
    if len(dtypes) != len(axes):
        raise ValueError("`dtypes` and `axes` must have the same length")

    # header
    print('femto performance benchmark')
    print("    femto %s; Numpy %s" % (ss.__version__, np.__version__))
    print("    Speed is NumPy time divided by femto time")
    print("    Score is harmonic mean of speeds")
    print('')
    header = [" "*4]
    header = ["".join(str(shape).split(" ")).center(11) for shape in shapes]
    header = [" "*6] + header
    print("".join(header))
    header = ["".join((str(dtype)).split(" ")).center(11)
              for dtype in dtypes]
    header = [" "*6] + header
    print("".join(header))
    header = ["".join(("axis=" + str(axis)).split(" ")).center(11)
              for axis in axes]
    header.append("   score")
    header = [" "*6] + header
    print("".join(header))

    suite = benchsuite(shapes, dtypes, axes, order, functions)
    for test in suite:
        name = test["name"].ljust(7)
        fmt = name + "%7.2f" + "%11.2f"*(len(shapes) - 1) + "%11.2f"
        speed = timer(test['statements'], test['setups'])
        speed.append(len(speed) / sum([1.0/s for s in speed]))
        print(fmt % tuple(speed))


def timer(statements, setups):
    speed = []
    if len(statements) != 2:
        raise ValueError("Two statements needed.")
    for setup in setups:
        with np.errstate(invalid='ignore'):
            t0 = autotimeit(statements[0], setup, repeat=3)
            t1 = autotimeit(statements[1], setup, repeat=3)
        speed.append(t1 / t0)
    return speed


def getarray(shape, dtype, order='C'):
    a = np.arange(np.prod(shape), dtype=dtype)
    rs = np.random.RandomState(shape)
    rs.shuffle(a)
    return np.array(a.reshape(*shape), order=order)


def benchsuite(shapes, dtypes, axes, order, functions):

    suite = []

    def getsetups(setup, shapes, dtypes, axes, order):
        template = """
        from femto.benchmark import getarray
        a = getarray(%s, '%s', '%s')
        axis=%s
        %s"""
        setups = []
        for shape, dtype, axis in zip(shapes, dtypes, axes):
            s = template % (str(shape), dtype, order, str(axis), setup)
            s = '\n'.join([line.strip() for line in s.split('\n')])
            setups.append(s)
        return setups

    # add functions to suite
    funcs = ss.get_functions(as_string=True)
    for func in funcs:
        if functions is not None and func not in functions:
            continue
        run = {}
        run['name'] = func
        run['statements'] = ["func(a, axis)", "a.sum(axis)"]
        setup = "from femto import %s as func" % func
        run['setups'] = getsetups(setup, shapes, dtypes, axes, order)
        suite.append(run)

    return suite


def autotimeit(stmt, setup='pass', repeat=3, mintime=0.2):
    timer = timeit.Timer(stmt, setup)
    number, time1 = autoscaler(timer, mintime)
    time2 = timer.repeat(repeat=repeat-1, number=number)
    return min(time2 + [time1]) / number


def autoscaler(timer, mintime):
    number = 1
    for i in range(12):
        time = timer.timeit(number)
        if time > mintime:
            return number, time
        number *= 10
    raise RuntimeError('function is too fast to test')


# ---------------------------------------------------------------------------

def bench_detailed(function='sum04'):
    """
    Benchmark a single function in detail or, optionally, all functions.

    Parameters
    ----------
    function : str, optional
        Name of function, as a string, to benchmark. Default ('nansum') is
        to benchmark bn.nansum. If `function` is 'all' then detailed
        benchmarks are run on all bottleneck functions.

    Returns
    -------
    A benchmark report is printed to stdout.

    """

    if function == 'all':
        # benchmark all femto functions
        funcs = ss.get_functions(as_string=True)
        funcs.sort()
        for func in funcs:
            bench_detailed(func)

    # header
    print('%s benchmark' % function)
    print("    femto %s; Numpy %s" % (ss.__version__, np.__version__))
    print("    Speed is NumPy time divided by femto time")
    print('')

    print("   Speed   Call            Array")
    suite = benchsuite_detailed(function)
    for test in suite:
        name = test["name"]
        speed = timer_detailed(test['statements'], test['setup'],
                               test['repeat'])
        print("%8.1f   %s   %s" % (speed, name[0].ljust(13), name[1]))


def benchsuite_detailed(function):

    # setup is called before each run of each function
    setup = """
        from femto import %s as ss_fn
        from numpy import sum as sl_fn

        from numpy.random import RandomState
        rand = RandomState(123).rand

        a = %s
    """
    setup = '\n'.join([s.strip() for s in setup.split('\n')])

    # create benchmark suite
    instructions = get_instructions()
    f = function
    suite = []
    for instruction in instructions:
        array = instruction[0]
        signature = instruction[1]
        repeat = instruction[2]
        run = {}
        run['name'] = [f + signature, array]
        run['statements'] = ["ss_fn" + signature, "sl_fn" + signature]
        run['setup'] = setup % (f, array)
        run['repeat'] = repeat
        suite.append(run)

    return suite


def timer_detailed(statements, setup, repeat=3):
    if len(statements) != 2:
        raise ValueError("Two statements needed.")
    with np.errstate(invalid='ignore'):
        t0 = autotimeit(statements[0], setup, repeat=repeat)
        t1 = autotimeit(statements[1], setup, repeat=repeat)
    speed = t1 / t0
    return speed


def get_instructions():

    instructions = [

        ("rand(10, 10)", "(a, 0)", 6),
        ("rand(10, 10)", "(a, 1)", 6),

        ("rand(100, 100)", "(a, 0)", 3),
        ("rand(100, 100)", "(a, 1)", 3),

        ("rand(1000, 1000)", "(a, 0)", 2),
        ("rand(1000, 1000)", "(a, 1)", 2),

        ("rand(1, 1000)", "(a, 0)", 3),
        ("rand(1, 1000)", "(a, 1)", 3),

        ("rand(100, 100, 100)", "(a, 0)", 2),
        ("rand(100, 100, 100)", "(a, 1)", 2),
        ("rand(100, 100, 100)", "(a, 2)", 2),

        ("rand(100000, 10)", "(a, 0)", 2),
        ("rand(100000, 10)", "(a, 1)", 2),

        ("rand(2000, 1000)[::2]", "(a, 0)", 2),
        ("rand(2000, 1000)[::2]", "(a, 1)", 2),

        ("rand(1000, 2000)[:,::2]", "(a, 0)", 2),
        ("rand(1000, 2000)[:,::2]", "(a, 1)", 2),

     ]

    return instructions
