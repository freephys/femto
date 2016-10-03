"Test reduce functions."

import warnings
import traceback

from nose.tools import ok_
import numpy as np
from numpy.testing import (assert_equal, assert_raises,
                           assert_array_almost_equal)

import some_sums as ss

DTYPES = [np.float64, np.float32, np.int64, np.int32]


def test_reduce():
    "test reduce functions"
    for func in ss.get_functions('reduce'):
        yield unit_maker, func


def arrays(dtypes, name):
    "Iterator that yields arrays to use for unit testing."

    # nan and inf
    nan = np.nan
    inf = np.inf
    yield np.array([inf, nan])
    yield np.array([inf, -inf])
    # yield np.array([nan, inf])  np.nanargmin can't handle this one

    # byte swapped
    yield np.array([1, 2, 3], dtype='>f4')
    yield np.array([1, 2, 3], dtype='<f4')

    # make sure slow is called
    yield np.array([1, 2, 3], dtype=np.float16)

    # regression tests
    yield np.array([0, 0, 0])  # nanargmax/nanargmin
    yield np.array([1, nan, nan, 2])  # nanmedian

    # ties
    yield np.array([0, 0, 0], dtype=np.float64)
    yield np.array([1, 1, 1], dtype=np.float64)

    # 0d input
    yield np.array(-9)
    yield np.array(0)
    yield np.array(9)
    yield np.array(-9.0)
    yield np.array(0.0)
    yield np.array(9.0)
    yield np.array(-inf)
    yield np.array(inf)
    yield np.array(nan)

    # Automate a bunch of arrays to test
    ss = {}
    ss[0] = {'size':  0, 'shapes': [(0,), (0, 0), (2, 0), (2, 0, 1)]}
    ss[1] = {'size':  8, 'shapes': [(8,)]}
    ss[2] = {'size': 12, 'shapes': [(2, 6), (3, 4)]}
    ss[3] = {'size': 16, 'shapes': [(2, 2, 4)]}
    ss[4] = {'size': 24, 'shapes': [(1, 2, 3, 4)]}
    for seed in (1, 2):
        rs = np.random.RandomState(seed)
        for ndim in ss:
            size = ss[ndim]['size']
            shapes = ss[ndim]['shapes']
            for dtype in dtypes:
                a = np.arange(size, dtype=dtype)
                if issubclass(a.dtype.type, np.inexact):
                    if name not in ('nanargmin', 'nanargmax'):
                        # numpy can't handle eg np.nanargmin([np.nan, np.inf])
                        idx = rs.rand(*a.shape) < 0.2
                        a[idx] = inf
                    idx = rs.rand(*a.shape) < 0.2
                    a[idx] = nan
                    idx = rs.rand(*a.shape) < 0.2
                    a[idx] *= -1
                rs.shuffle(a)
                for shape in shapes:
                    yield a.reshape(shape)


def unit_maker(func, decimal=5):
    "Test that ss.xxx gives the same output as ss.slow.xxx."
    fmt = '\nfunc %s | input %s (%s) | shape %s | axis %s\n'
    fmt += '\nInput array:\n%s\n'
    name = func.__name__
    func0 = eval('ss.slow.%s' % name)
    for i, a in enumerate(arrays(DTYPES, name)):
        if a.ndim == 0:
            axes = [None]  # numpy can't handle e.g. np.nanmean(9, axis=-1)
        else:
            axes = list(range(-1, a.ndim)) + [None]
        for axis in axes:
            actual = 'Crashed'
            desired = 'Crashed'
            actualraised = False
            try:
                # do not use a.copy() here because it will C order the array
                actual = func(a, axis=axis)
            except:
                actualraised = True
            desiredraised = False
            try:
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    desired = func0(a, axis=axis)
            except:
                desiredraised = True
            if actualraised and desiredraised:
                pass
            else:
                tup = (name, 'a'+str(i), str(a.dtype), str(a.shape),
                       str(axis), a)
                err_msg = fmt % tup
                if actualraised != desiredraised:
                    if actualraised:
                        fmt2 = '\nss.%s raised\nss.slow.%s ran\n\n%s'
                    else:
                        fmt2 = '\nss.%s ran\nss.slow.%s raised\n\n%s'
                    msg = fmt2 % (name, name, traceback.format_exc())
                    err_msg += msg
                    ok_(False, err_msg)
                assert_array_almost_equal(actual, desired, decimal, err_msg)
                err_msg += '\n dtype mismatch %s %s'
                if hasattr(actual, 'dtype') and hasattr(desired, 'dtype'):
                    da = actual.dtype
                    dd = desired.dtype
                    assert_equal(da, dd, err_msg % (da, dd))


# ---------------------------------------------------------------------------
# Test with arrays that are not C ordered

def test_strides():
    "test reduce functions with non-C ordered arrays"
    for func in ss.get_functions('reduce'):
        yield unit_maker_strides, func


def arrays_strides(dtypes=DTYPES):
    "Iterator that yields non-C orders arrays."

    # 1d
    for dtype in dtypes:
        a = np.arange(12).astype(dtype)
        for start in range(3):
            for step in range(1, 3):
                yield a[start::step]  # don't use astype here; copy created

    # 2d
    for dtype in dtypes:
        a = np.arange(12).reshape(4, 3).astype(dtype)
        yield a[::2]
        yield a[:, ::2]
        yield a[::2][:, ::2]

    # 3d
    for dtype in dtypes:
        a = np.arange(24).reshape(2, 3, 4).astype(dtype)
        for start in range(2):
            for step in range(1, 2):
                yield a[start::step]
                yield a[:, start::step]
                yield a[:, :, start::step]
                yield a[start::step][::2]
                yield a[start::step][::2][:, ::2]


def unit_maker_strides(func, decimal=5):
    "Test that ss.xxx gives the same output as ss.slow.xxx."
    fmt = '\nfunc %s | input %s (%s) | shape %s | axis %s\n'
    fmt += '\nInput array:\n%s\n'
    fmt += '\nStrides: %s\n'
    fmt += '\nFlags: \n%s\n'
    name = func.__name__
    func0 = eval('ss.slow.%s' % name)
    for i, a in enumerate(arrays_strides()):
        if a.ndim == 0:
            axes = [None]  # numpy can't handle e.g. np.nanmean(9, axis=-1)
        else:
            axes = list(range(-1, a.ndim)) + [None]
        for axis in axes:
            # do not use a.copy() here because it will C order the array
            actual = func(a, axis=axis)
            desired = func0(a, axis=axis)
            tup = (name, 'a'+str(i), str(a.dtype), str(a.shape),
                   str(axis), a, a.strides, a.flags)
            err_msg = fmt % tup
            assert_array_almost_equal(actual, desired, decimal, err_msg)
            err_msg += '\n dtype mismatch %s %s'


# ---------------------------------------------------------------------------
# Test argument parsing

def test_arg_parsing():
    "test argument parsing"
    for func in ss.get_functions('reduce'):
        yield unit_maker_argparse, func


def unit_maker_argparse(func, decimal=5):
    "test argument parsing."

    name = func.__name__
    func0 = eval('ss.slow.%s' % name)

    a = np.array([1., 2, 3])

    fmt = '\n%s' % func
    fmt += '%s\n'
    fmt += '\nInput array:\n%s\n' % a

    actual = func(a)
    desired = func0(a)
    err_msg = fmt % "(a)"
    assert_array_almost_equal(actual, desired, decimal, err_msg)

    actual = func(a, 0)
    desired = func0(a, 0)
    err_msg = fmt % "(a, 0)"
    assert_array_almost_equal(actual, desired, decimal, err_msg)

    actual = func(a, None)
    desired = func0(a, None)
    err_msg = fmt % "(a, None)"
    assert_array_almost_equal(actual, desired, decimal, err_msg)

    actual = func(a, axis=0)
    desired = func0(a, axis=0)
    err_msg = fmt % "(a, axis=0)"
    assert_array_almost_equal(actual, desired, decimal, err_msg)

    actual = func(a, axis=None)
    desired = func0(a, axis=None)
    err_msg = fmt % "(a, axis=None)"
    assert_array_almost_equal(actual, desired, decimal, err_msg)

    actual = func(a=a)
    desired = func0(a=a)
    err_msg = fmt % "(a)"
    assert_array_almost_equal(actual, desired, decimal, err_msg)

    # regression test: make sure len(kwargs) == 0 doesn't raise
    args = (a, 0)
    kwargs = {}
    func(*args, **kwargs)


def test_arg_parse_raises():
    "test argument parsing raises in reduce"
    for func in ss.get_functions('reduce'):
        yield unit_maker_argparse_raises, func


def unit_maker_argparse_raises(func):
    "test argument parsing raises in reduce"
    a = np.array([1., 2, 3])
    assert_raises(TypeError, func)
    assert_raises(TypeError, func, axis=a)
    assert_raises(TypeError, func, a, axis=0, extra=0)
    assert_raises(TypeError, func, a, axis=0, a=a)
    assert_raises(TypeError, func, a, 0, 0, 0, 0, 0)
    assert_raises(TypeError, func, a, axis='0')
    if func.__name__ not in ('nanstd', 'nanvar'):
        assert_raises(TypeError, func, a, ddof=0)
    assert_raises(TypeError, func, a, a)
    # assert_raises(TypeError, func, None) results vary


# ---------------------------------------------------------------------------
# test loop unrolling


def test_unrolling():
    "test loop unrolling"
    for func in ss.get_functions('reduce'):
        yield unit_maker_unroll, func


def unroll_arrays(dtypes, name):
    "Iterator that yields arrays to use for unit testing."
    for ndim in (1, 2):
        rs = np.random.RandomState(ndim)
        for length in range(20):
            for dtype in dtypes:
                a = np.arange(length * ndim, dtype=dtype)
                rs.shuffle(a)
                if ndim == 1:
                    yield a
                else:
                    yield a.reshape(2, -1)


def unit_maker_unroll(func, decimal=5):
    "Test that ss.xxx gives the same output as ss.slow.xxx."
    fmt = '\nfunc %s | input %s (%s) | shape %s | axis %s\n'
    fmt += '\nInput array:\n%s\n'
    name = func.__name__
    func0 = eval('ss.slow.%s' % name)
    for i, a in enumerate(unroll_arrays(DTYPES, name)):
        if a.ndim == 0:
            axes = [None]  # numpy can't handle e.g. np.nanmean(9, axis=-1)
        else:
            axes = list(range(-1, a.ndim)) + [None]
        for axis in axes:
            actual = 'Crashed'
            desired = 'Crashed'
            actualraised = False
            try:
                # do not use a.copy() here because it will C order the array
                actual = func(a, axis=axis)
            except:
                actualraised = True
            desiredraised = False
            try:
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    desired = func0(a, axis=axis)
            except:
                desiredraised = True
            if actualraised and desiredraised:
                pass
            else:
                tup = (name, 'a'+str(i), str(a.dtype), str(a.shape),
                       str(axis), a)
                err_msg = fmt % tup
                if actualraised != desiredraised:
                    if actualraised:
                        fmt2 = '\nss.%s raised\nss.slow.%s ran\n\n%s'
                    else:
                        fmt2 = '\nss.%s ran\nss.slow.%s raised\n\n%s'
                    msg = fmt2 % (name, name, traceback.format_exc())
                    err_msg += msg
                    ok_(False, err_msg)
                assert_array_almost_equal(actual, desired, decimal, err_msg)
                err_msg += '\n dtype mismatch %s %s'
                if hasattr(actual, 'dtype') and hasattr(desired, 'dtype'):
                    da = actual.dtype
                    dd = desired.dtype
                    assert_equal(da, dd, err_msg % (da, dd))
