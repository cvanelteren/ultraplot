#!/usr/bin/env python3
"""
Defines various axis scales, locators, and formatters. Also "registers"
the locator and formatter names, so that they can be called selected with
the `~proplot.axes.CartesianAxes.format` method.
"""
import re
from .utils import _notNone
from .rctools import rc
from numbers import Number
from fractions import Fraction
import numpy as np
import numpy.ma as ma
import warnings
import matplotlib.dates as mdates
import matplotlib.projections as mproj
import matplotlib.ticker as mticker
import matplotlib.scale as mscale
import matplotlib.transforms as mtransforms
__all__ = [
    'formatters', 'locators', 'scales',
    'Formatter', 'Locator', 'Scale',
    'AutoFormatter', 'CutoffScale', 'ExpScale',
    'FracFormatter', 'FuncScale',
    'InverseScale',
    'LogScale',
    'MercatorLatitudeScale', 'PowerScale', 'SimpleFormatter',
    'SineLatitudeScale',
    'SymmetricalLogScale',
    ]

# Scale preset names and positional args
SCALE_PRESETS = {
    'quadratic': ('power', 2,),
    'cubic':     ('power', 3,),
    'quartic':   ('power', 4,),
    'height':    ('exp', np.e, -1/7, 1013.25, True),
    'pressure':  ('exp', np.e, -1/7, 1013.25, False),
    'db':        ('exp', 10, 1, 0.1, True),
    'idb':       ('exp', 10, 1, 0.1, False),
    'np':        ('exp', np.e, 1, 1, True),
    'inp':       ('exp', np.e, 1, 1, False),
    }

#-----------------------------------------------------------------------------#
# Helper functions for instantiating arbitrary classes
#-----------------------------------------------------------------------------#
def Locator(locator, *args, **kwargs):
    """
    Returns a `~matplotlib.ticker.Locator` instance, used to interpret the
    `xlocator`, `xlocator_kw`, `ylocator`, `ylocator_kw`, `xminorlocator`,
    `xminorlocator_kw`, `yminorlocator`, and `yminorlocator_kw` arguments when
    passed to `~proplot.axes.CartesianAxes.format`, and the `locator`, `locator_kw`
    `minorlocator`, and `minorlocator_kw` arguments when passed to colorbar
    methods wrapped by `~proplot.wrappers.colorbar_wrapper`.

    Parameters
    ----------
    locator : str, float, or list of float
        If number, specifies the *multiple* used to define tick separation.
        Returns a `~matplotlib.ticker.MultipleLocator` instance.

        If list of numbers, these points are ticked. Returns a
        `~matplotlib.ticker.FixedLocator` instance.

        If string, a dictionary lookup is performed (see below table).

        ======================  ==========================================  =========================================================================================
        Key                     Class                                       Description
        ======================  ==========================================  =========================================================================================
        ``'null'``, ``'none'``  `~matplotlib.ticker.NullLocator`            No ticks
        ``'auto'``              `~matplotlib.ticker.AutoLocator`            Major ticks at sensible locations
        ``'minor'``             `~matplotlib.ticker.AutoMinorLocator`       Minor ticks at sensible locations
        ``'date'``              `~matplotlib.dates.AutoDateLocator`         Default tick locations for datetime axes
        ``'log'``               `~matplotlib.ticker.LogLocator` preset      For log-scale axes, ticks on each power of the base
        ``'logminor'``          `~matplotlib.ticker.LogLocator` preset      For log-scale axes, ticks on the 1st through 9th multiples of each power of the base
        ``'maxn'``              `~matplotlib.ticker.MaxNLocator`            No more than ``N`` ticks at sensible locations
        ``'linear'``            `~matplotlib.ticker.LinearLocator`          Exactly ``N`` ticks encompassing the axis limits, spaced as ``numpy.linspace(lo, hi, N)``
        ``'multiple'``          `~matplotlib.ticker.MultipleLocator`        Ticks every ``N`` step away from zero
        ``'fixed'``             `~matplotlib.ticker.FixedLocator`           Ticks at these exact locations
        ``'index'``             `~matplotlib.ticker.IndexLocator`           Ticks on the non-negative integers
        ``'symmetric'``         `~matplotlib.ticker.SymmetricalLogLocator`  Ticks for symmetrical log-scale axes
        ``'logit'``             `~matplotlib.ticker.LogitLocator`           Ticks for logit-scale axes
        ``'year'``              `~matplotlib.dates.YearLocator`             Ticks every ``N`` years
        ``'month'``             `~matplotlib.dates.MonthLocator`            Ticks every ``N`` months
        ``'weekday'``           `~matplotlib.dates.WeekdayLocator`          Ticks every ``N`` weekdays
        ``'day'``               `~matplotlib.dates.DayLocator`              Ticks every ``N`` days
        ``'hour'``              `~matplotlib.dates.HourLocator`             Ticks every ``N`` hours
        ``'minute'``            `~matplotlib.dates.MinuteLocator`           Ticks every ``N`` minutes
        ``'second'``            `~matplotlib.dates.SecondLocator`           Ticks every ``N`` seconds
        ``'microsecond'``       `~matplotlib.dates.MicrosecondLocator`      Ticks every ``N`` microseconds
        ======================  ==========================================  =========================================================================================

    *args, **kwargs
        Passed to the `~matplotlib.ticker.Locator` class.

    Returns
    -------
    `~matplotlib.ticker.Locator`
        A `~matplotlib.ticker.Locator` instance.
    """
    if isinstance(locator, mticker.Locator):
        return locator
    # Pull out extra args
    if np.iterable(locator) and not isinstance(locator, str) and not all(isinstance(num, Number) for num in locator):
        locator, args = locator[0], (*locator[1:], *args)
    # Get the locator
    if isinstance(locator, str): # dictionary lookup
        # Shorthands and defaults
        if locator == 'logminor':
            locator = 'log'
            kwargs.setdefault('subs', np.arange(10))
        elif locator == 'index':
            args = args or (1,)
            if len(args) == 1:
                args = (*args, 0)
        # Lookup
        if locator not in locators:
            raise ValueError(f'Unknown locator {locator!r}. Options are {", ".join(locators.keys())}.')
        locator = locators[locator](*args, **kwargs)
    elif isinstance(locator, Number): # scalar variable
        locator = mticker.MultipleLocator(locator, *args, **kwargs)
    elif np.iterable(locator):
        locator = mticker.FixedLocator(np.sort(locator), *args, **kwargs) # not necessary
    else:
        raise ValueError(f'Invalid locator {locator!r}.')
    return locator

def Formatter(formatter, *args, date=False, **kwargs):
    r"""
    Returns a `~matplotlib.ticker.Formatter` instance, used to interpret the
    `xformatter`, `xformatter_kw`, `yformatter`, and `yformatter_kw` arguments
    when passed to `~proplot.axes.CartesianAxes.format`, and the `formatter`
    and `formatter_kw` arguments when passed to colorbar methods wrapped by
    `~proplot.wrappers.colorbar_wrapper`.

    Parameters
    ----------
    formatter : str, list of str, or function
        If list of strings, ticks are labeled with these strings. Returns a
        `~matplotlib.ticker.FixedFormatter` instance.

        If function, labels will be generated using this function. Returns a
        `~matplotlib.ticker.FuncFormatter` instance.

        If string, there are 4 possibilities:

        1. If string contains ``'%'`` and `date` is ``False``, ticks will be formatted
           using the C-notation ``string % number`` method. See `this page
           <https://docs.python.org/3.4/library/string.html#format-specification-mini-language>`__
           for a review.
        2. If string contains ``'%'`` and `date` is ``True``, datetime
           ``string % number`` formatting is used. See `this page
           <https://docs.python.org/3/library/datetime.html#strftime-strptime-behavior>`__
           for a review.
        3. If string contains ``{x}`` or ``{x:...}``, ticks will be
           formatted by calling ``string.format(x=number)``.
        4. In all other cases, a dictionary lookup is performed
           (see below table).

        =========================  ============================================  ============================================================================================================================================
        Key                        Class                                         Description
        =========================  ============================================  ============================================================================================================================================
        ``'null'``, ``'none'``     `~matplotlib.ticker.NullFormatter`            No tick labels
        ``'auto'``, ``'default'``  `AutoFormatter`                               New default tick labels for axes
        ``'simple'``               `SimpleFormatter`                             New default tick labels for e.g. contour labels
        ``'frac'``                 `FracFormatter`                               Rational fractions
        ``'date'``                 `~matplotlib.dates.AutoDateFormatter`         Default tick labels for datetime axes
        ``'datestr'``              `~matplotlib.dates.DateFormatter`             Date formatting with C-style ``string % format`` notation
        ``'concise'``              `~matplotlib.dates.ConciseDateForamtter`      More concise default tick labels, introduced in `matplotlib 3.1 <https://matplotlib.org/3.1.0/users/whats_new.html#concisedateformatter>`__
        ``'scalar'``               `~matplotlib.ticker.ScalarFormatter`          Old default tick labels for axes
        ``'strmethod'``            `~matplotlib.ticker.StrMethodFormatter`       From the ``string.format`` method
        ``'formatstr'``            `~matplotlib.ticker.FormatStrFormatter`       From C-style ``string % format`` notation
        ``'log'``, ``'sci'``       `~matplotlib.ticker.LogFormatterSciNotation`  For log-scale axes with scientific notation
        ``'math'``                 `~matplotlib.ticker.LogFormatterMathtext`     For log-scale axes with math text
        ``'logit'``                `~matplotlib.ticker.LogitFormatter`           For logistic-scale axes
        ``'eng'``                  `~matplotlib.ticker.EngFormatter`             Engineering notation
        ``'percent'``              `~matplotlib.ticker.PercentFormatter`         Trailing percent sign
        ``'fixed'``                `~matplotlib.ticker.FixedFormatter`           List of strings
        ``'index'``                `~matplotlib.ticker.IndexFormatter`           List of strings corresponding to non-negative integer positions along the axis
        ``'theta'``                `~matplotlib.proj.ThetaFormatter`             Formats radians as degrees, with a degree symbol
        ``'pi'``                   `FracFormatter` preset                        Fractions of :math:`\pi`
        ``'e'``                    `FracFormatter` preset                        Fractions of *e*
        ``'deg'``                  `SimpleFormatter` preset                      Trailing degree symbol
        ``'deglon'``               `SimpleFormatter` preset                      Trailing degree symbol and cardinal "WE" indicator
        ``'deglat'``               `SimpleFormatter` preset                      Trailing degree symbol and cardinal "SN" indicator
        ``'lon'``                  `SimpleFormatter` preset                      Cardinal "WE" indicator
        ``'lat'``                  `SimpleFormatter` preset                      Cardinal "SN" indicator
        =========================  ============================================  ============================================================================================================================================

    date : bool, optional
        Toggles the behavior when `formatter` contains a ``'%'`` sign (see
        above).
    *args, **kwargs
        Passed to the `~matplotlib.ticker.Formatter` class.

    Returns
    -------
    `~matplotlib.ticker.Formatter`
        A `~matplotlib.ticker.Formatter` instance.
    """
    if isinstance(formatter, mticker.Formatter): # formatter object
        return formatter
    # Pull out extra args
    if np.iterable(formatter) and not isinstance(formatter, str) and not all(isinstance(item, str) for item in formatter):
        formatter, args = formatter[0], [*formatter[1:], *args]
    # Get the formatter
    if isinstance(formatter, str): # assumption is list of strings
        # Format strings
        if re.search(r'{x?(:.+)?}', formatter):
            formatter = mticker.StrMethodFormatter(formatter, *args, **kwargs) # new-style .format() form
        elif '%' in formatter:
            if date:
                formatter = mdates.DateFormatter(formatter, *args, **kwargs) # %-style, dates
            else:
                formatter = mticker.FormatStrFormatter(formatter, *args, **kwargs) # %-style, numbers
        else:
            # Fraction shorthands
            if formatter in ('pi', 'e'):
                if formatter == 'pi':
                    kwargs.update({'symbol': r'$\pi$', 'number': np.pi})
                else:
                    kwargs.update({'symbol': '$e$', 'number': np.e})
                formatter = 'frac'
            # Cartographic shorthands
            if formatter in ('deg', 'deglon', 'deglat', 'lon', 'lat'):
                negpos, suffix = None, None
                if 'deg' in formatter:
                    suffix = '\N{DEGREE SIGN}'
                if 'lat' in formatter:
                    negpos = 'SN'
                if 'lon' in formatter:
                    negpos = 'WE'
                kwargs.update({'suffix':suffix, 'negpos':negpos})
                formatter = 'simple'
            # Lookup
            if formatter not in formatters:
                raise ValueError(f'Unknown formatter {formatter!r}. Options are {", ".join(formatters.keys())}.')
            formatter = formatters[formatter](*args, **kwargs)
    elif callable(formatter):
        formatter = mticker.FuncFormatter(formatter, *args, **kwargs)
    elif np.iterable(formatter): # list of strings on the major ticks, wherever they may be
        formatter = mticker.FixedFormatter(formatter)
    else:
        raise ValueError(f'Invalid formatter {formatter!r}.')
    return formatter

def Scale(scale, *args, **kwargs):
    """
    Returns a `~matplotlib.scale.ScaleBase` instance, used to interpret the
    `xscale`, `xscale_kw`, `yscale`, and `yscale_kw` arguments when passed to
    `~proplot.axes.CartesianAxes.format`.

    Parameters
    ----------
    scale : str, (str, ...), or class
        The registered scale name or scale "preset" (see below table). If a
        tuple or list is passed, the items after the string are passed to
        the scale as positional arguments.

        =================  ===============================  ===========================================================================================================
        Key                Class                            Description
        =================  ===============================  ===========================================================================================================
        ``'linear'``       `~matplotlib.scale.LinearScale`  Linear
        ``'log'``          `LogScale`                       Logarithmic
        ``'symlog'``       `SymmetricalLogScale`            Logarithmic beyond finite space around zero
        ``'logit'``        `~matplotlib.scale.LogitScale`   Logistic
        ``'inverse'``      `InverseScale`                   Inverse
        ``'function'``     `FuncScale`                      Scale from arbitrary forward and backwards functions
        ``'sine'``         `SineLatitudeScale`              Sine function (in degrees)
        ``'mercator'``     `MercatorLatitudeScale`          Mercator latitude function (in degrees)
        ``'exp'``          `ExpScale`                       Arbitrary exponential function
        ``'power'``        `PowerScale`                     Arbitrary power function
        ``'cutoff'``       `CutoffScale`                    Arbitrary linear transformations
        ``'quadratic'``    `PowerScale` (preset)            Quadratic function, generated with ``PowerScale(axis, 2)``
        ``'cubic'``        `PowerScale` (preset)            Cubic function, generated with ``PowerScale(axis, 3)``
        ``'quartic'`       `PowerScale` (preset)            Cubic function, generated with ``PowerScale(axis, 4)``
        ``'pressure'``     `ExpScale` (preset)              Expresses height (in km) linear in pressure, generated with ``ExpScale(axis, np.e, -1/7, 1013.25, False)``
        ``'height'``       `ExpScale` (preset)              Expresses pressure (in mb) linear in height, generated with ``ExpScale(axis, np.e, -1/7, 1013.25, True)``
        ``'db'``           `ExpScale` (preset)              Ratio expressed as `decibels <https://en.wikipedia.org/wiki/Decibel>`__.
        ``'np'``           `ExpScale` (preset)              Ratio expressed as `nepers <https://en.wikipedia.org/wiki/Neper>`__.
        ``'idb'``          `ExpScale` (preset)              `Decibels <https://en.wikipedia.org/wiki/Decibel>`__ expressed as ratio.
        ``'inp'``          `ExpScale` (preset)              `Nepers <https://en.wikipedia.org/wiki/Neper>`__ expressed as ratio.
        =================  ===============================  ===========================================================================================================

    *args, **kwargs
        Passed to the `~matplotlib.scale.ScaleBase` class.

    Returns
    -------
    `~matplotlib.scale.ScaleBase`
        The scale instance.
    """
    if isinstance(scale, type):
        # User-supplied scale class
        mscale.register_scale(scale) # ensure it is registered!
    else:
        # Pull out extra args
        if np.iterable(scale) and not isinstance(scale, str):
            scale, args = scale[0], (*scale[1:], *args)
        if not isinstance(scale, str):
            raise ValueError(f'Invalid scale name {scale!r}. Must be string.')
        # Scale presets
        if scale in SCALE_PRESETS:
            if args or kwargs:
                warnings.warn(f'Scale {scale!r} is a scale *preset*. Ignoring positional argument(s): {args} and keyword argument(s): {kwargs}. ')
            scale, *args = SCALE_PRESETS[scale]
        # Get scale
        scale = scale.lower()
        if scale in scales:
            scale = scales[scale]
        else:
            raise ValueError(f'Unknown scale {scale!r}. Options are {", ".join(scales.keys())}.')
    # Initialize scale (see _dummy_axis comments)
    axis = _dummy_axis()
    return scale(axis, *args, **kwargs)

#-----------------------------------------------------------------------------#
# Formatting classes for mapping numbers (axis ticks) to formatted strings
# Create pseudo-class functions that actually return auto-generated formatting
# classes by passing function references to Funcformatter
#-----------------------------------------------------------------------------#
class AutoFormatter(mticker.ScalarFormatter):
    """
    The new default formatter, a simple wrapper around
    `~matplotlib.ticker.ScalarFormatter`. Differs from
    `~matplotlib.ticker.ScalarFormatter` in the following ways:

    1. Trims trailing zeros if any exist.
    2. Allows user to specify *range* within which major tick marks
       are labelled.
    3. Allows user to add arbitrary prefix or suffix to every
       tick label string.

    """
    def __init__(self, *args,
        zerotrim=None, precision=None, tickrange=None,
        prefix=None, suffix=None, **kwargs):
        """
        Parameters
        ----------
        zerotrim : bool, optional
            Whether to trim trailing zeros.
            Default is :rc:`axes.formatter.zerotrim`.
        precision : float, optional
            The maximum number of digits after the decimal point.
        tickrange : (float, float), optional
            Range within which major tick marks are labelled.
        prefix, suffix : str, optional
            Optional prefix and suffix for all strings.
        *args, **kwargs
            Passed to `matplotlib.ticker.ScalarFormatter`.
        """
        tickrange = tickrange or (-np.inf, np.inf)
        super().__init__(*args, **kwargs)
        zerotrim = _notNone(zerotrim, rc.get('axes.formatter.zerotrim'))
        self._maxprecision = precision
        self._zerotrim = zerotrim
        self._tickrange = tickrange
        self._prefix = prefix or ''
        self._suffix = suffix or ''

    def __call__(self, x, pos=None):
        """
        Parameters
        ----------
        x : float
            The value.
        pos : float, optional
            The position.
        """
        # Tick range limitation
        eps = abs(x)/1000
        tickrange = self._tickrange
        if (x + eps) < tickrange[0] or (x - eps) > tickrange[1]:
            return '' # avoid some ticks
        # Normal formatting
        string = super().__call__(x, pos)
        if self._maxprecision is not None and '.' in string:
            head, tail = string.split('.')
            string = head + '.' + tail[:self._maxprecision]
        if self._zerotrim:
            string = re.sub(r'\.0+$', '', string)
            string = re.sub(r'^(.*\..*?)0+$', r'\1', string)
        string = re.sub(r'^[−-]0$', '0', string) # '-0' to '0'; necessary?
        # Prefix and suffix
        prefix = ''
        if string and string[0] in '−-': # unicode minus or hyphen
            prefix, string = string[0], string[1:]
        return prefix + self._prefix + string + self._suffix

def SimpleFormatter(*args, precision=6,
        prefix=None, suffix=None, negpos=None,
        **kwargs):
    """
    Replicates features of `AutoFormatter`, but as a simpler
    `~matplotlib.ticker.FuncFormatter` instance. This is more suitable for
    arbitrary number formatting not necessarily associated with any
    `~matplotlib.axis.Axis` instance, e.g. labelling contours.

    Parameters
    ----------
    precision : int, optional
        Maximum number of digits after the decimal point.
    prefix, suffix : str, optional
        Optional prefix and suffix for all strings.
    negpos : str, optional
        Length-2 string that indicates suffix for "negative" and "positive"
        numbers, meant to replace the minus sign. This is useful for
        indicating cardinal geographic coordinates.
    """
    prefix = prefix or ''
    suffix = suffix or ''
    def f(x, pos):
        # Apply suffix if not on equator/prime meridian
        if not negpos:
            negpos_ = ''
        elif x > 0:
            negpos_ = negpos[1]
        else:
            x *= -1
            negpos_ = negpos[0]
        # Finally use default formatter
        string = f'{{:.{precision}f}}'.format(x)
        string = re.sub(r'\.0+$', '', string)
        string = re.sub(r'^(.*\..*?)0+$', r'\1', string) # note the non-greedy secondary glob!
        if string == '-0':
            string = '0'
        string = string.replace('-', '\N{MINUS SIGN}')
        return prefix + string + suffix + negpos_
    return mticker.FuncFormatter(f)

def FracFormatter(symbol='', number=1):
    r"""
    Returns a `~matplotlib.ticker.FuncFormatter` that formats numbers as
    fractions or multiples of some value, e.g. a physical constant.

    This is powered by the python builtin `~fractions.Fraction` class.
    We account for floating point errors using the
    `~fractions.Fraction.limit_denominator` method.

    Parameters
    ----------
    symbol : str
        The symbol, e.g. ``r'$\pi$'``. Default is ``''``.
    number : float
        The value, e.g. `numpy.pi`. Default is ``1``.
    """
    def f(x, pos): # must accept location argument
        frac = Fraction(x/number).limit_denominator()
        if x == 0: # zero
            string = '0'
        elif frac.denominator == 1: # denominator is one
            if frac.numerator == 1 and symbol:
                string = f'{symbol:s}'
            elif frac.numerator == -1 and symbol:
                string = f'-{symbol:s}'
            else:
                string = f'{frac.numerator:d}{symbol:s}'
        elif frac.numerator == 1 and symbol: # numerator is +/-1
            string = f'{symbol:s}/{frac.denominator:d}'
        elif frac.numerator == -1 and symbol:
            string = f'-{symbol:s}/{frac.denominator:d}'
        else: # and again make sure we use unicode minus!
            string = f'{frac.numerator:d}{symbol:s}/{frac.denominator:d}'
        return string.replace('-', '\N{MINUS SIGN}')
    # And create FuncFormatter class
    return mticker.FuncFormatter(f)

#-----------------------------------------------------------------------------#
# Simple scale overrides
#-----------------------------------------------------------------------------#
class _dummy_axis(object):
    """Dummy axis used to initialize scales."""
    # See notes in source code for `~matplotlib.scale.ScaleBase`. All scales
    # accept 'axis' for backwards-compatibility reasons, but it is *virtually
    # unused* except to check for the `axis_name` attribute in log scales to
    # interpret input keyword args!
    # TODO: Submit matplotlib pull request! How has no one fixed this already!
    axis_name = 'x'

def _scale_factory(scale, axis, *args, **kwargs):
    """If `scale` is a `~matplotlib.scale.ScaleBase` instance, nothing is
    done. If it is a registered scale name, that scale is looked up and
    instantiated."""
    if isinstance(scale, mscale.ScaleBase):
        if args or kwargs:
            warnings.warn(f'Ignoring args {args} and keyword args {kwargs}.')
        return scale # do nothing
    else:
        scale = scale.lower()
        if scale not in scales:
            raise ValueError(f'Unknown scale {scale!r}. Options are {", ".join(scales.keys())}.')
        return scales[scale](axis, *args, **kwargs)

def _parse_logscale_args(kwargs, *keys):
    """Parses args for `LogScale` and `SymmetricalLogScale` that
    inexplicably require ``x`` and ``y`` suffixes by default."""
    for key in keys:
        value = _notNone( # issues warning when multiple args passed!
            kwargs.pop(key, None),
            kwargs.pop(key + 'x', None),
            kwargs.pop(key + 'y', None),
            None, names=(key, key + 'x', key + 'y'),
            )
        if value is not None: # _dummy_axis axis_name is 'x'
            kwargs[key + 'x'] = value
    return kwargs

class LogScale(mscale.LogScale):
    """
    As with `~matplotlib.scale.LogScale`, but fixes the inexplicable
    choice to have separate "``x``" and "``y``" versions of each keyword argument.
    """
    name = 'log'
    def __init__(self, axis, **kwargs):
        """
        Parameters
        ----------
        base : float, optional
            The base of the logarithm. Default is ``10``.
        nonpos : {'mask', 'clip'}, optional
            Non-positive values in *x* or *y* can be masked as
            invalid, or clipped to a very small positive number.
        subs : list of int, optional
            Default tick locations are on these multiples of each power
            of the base. For example, ``subs=(1,2,5)`` draws ticks on 1, 2, 5,
            10, 20, 50, 100, 200, 500, etc.
        basex, basey, nonposx, nonposy, subsx, subsy
            Aliases for the above keywords. These used to be conditional
            on the *name* of the axis...... yikes.
        """
        kwargs = _parse_logscale_args(kwargs,
            'base', 'nonpos', 'subs')
        super().__init__(axis, **kwargs)

class SymmetricalLogScale(mscale.SymmetricalLogScale):
    """
    As with `~matplotlib.scale.SymmetricLogScale`, but fixes the inexplicable
    choice to have separate "``x``" and "``y``" versions of each keyword argument.
    """
    name = 'symlog'
    def __init__(self, axis, **kwargs):
        """
        Parameters
        ----------
        base : float, optional
            The base of the logarithm. Default is ``10``.
        linthresh : float, optional
            Defines the range ``(-linthresh, linthresh)``, within which the
            plot is linear.  This avoids having the plot go to infinity around
            zero. Defaults to 2.
        linscale : float, optional
            This allows the linear range ``(-linthresh, linthresh)`` to be
            stretched relative to the logarithmic range. Its value is the
            number of decades to use for each half of the linear range. For
            example, when `linscale` is ``1`` (the default), the space used
            for the positive and negative halves of the linear range will be
            equal to one decade in the logarithmic range.
        subs : sequence of int, optional
            Default minor tick locations are on these multiples of each power
            of the base. For example, ``subs=[1,2,5]`` draws ticks on 1, 2, 5,
            10, 20, 50, 100, 200, 500, etc.
        basex, basey, linthreshx, linthreshy, linscalex, linscaley, subsx, subsy
            Aliases for the above keywords. These used to be conditional
            on the *name* of the axis...... yikes.
        """
        kwargs = _parse_logscale_args(kwargs,
            'base', 'linthresh', 'linscale', 'subs')
        super().__init__(axis, **kwargs)

#-----------------------------------------------------------------------------#
# Scales from functions
#-----------------------------------------------------------------------------#
class FuncScale(mscale.ScaleBase):
    """Arbitrary scale with user-supplied forward and inverse functions and
    arbitrary additional transform applied thereafter. Input is a tuple
    of functions and, optionally, a `~matplotlib.transforms.Transform` or
    `~matplotlib.scale.ScaleBase` instance."""
    name = 'function'
    """The registered scale name."""
    def __init__(self, axis, functions, transform=None):
        """
        Parameters
        ----------
        axis : `~matplotlib.axis.Axis`
            The axis, required for compatibility reasons.
        functions : (function, function)
            Length-2 tuple of forward and inverse functions.
        transform : `~matplotlib.transforms.Transform`, optional
            Optional transform applied after the forward function
            and before the inverse function.
        """
        forward, inverse = functions
        trans = FuncTransform(forward, inverse)
        if transform is not None:
            if isinstance(transform, mtransforms.Transform):
                trans = trans + transform
            else:
                raise ValueError(f'transform {transform!r} must be a Transform instance, not {type(transform)!r}.')
        self._transform = trans
    def get_transform(self):
        return self._transform
    def set_default_locators_and_formatters(self, axis):
        axis.set_major_locator(mticker.AutoLocator())
        axis.set_major_formatter(mticker.ScalarFormatter())
        axis.set_minor_formatter(mticker.NullFormatter())
        # update the minor locator for x and y axis based on rcParams
        if rc.get('xtick.minor.visible') or rc.get('ytick.minor.visible'):
            axis.set_minor_locator(mticker.AutoMinorLocator())
        else:
            axis.set_minor_locator(mticker.NullLocator())

class FuncTransform(mtransforms.Transform):
    # Arbitrary forward and inverse transform
    # Mostly copied from matplotlib
    input_dims = 1
    output_dims = 1
    is_separable = True
    has_inverse = True
    def __init__(self, forward, inverse):
        super().__init__()
        if callable(forward) and callable(inverse):
            self._forward = forward
            self._inverse = inverse
        else:
            raise ValueError('arguments to FuncTransform must be functions')
    def transform_non_affine(self, values):
        return self._forward(values)
    def inverted(self):
        return FuncTransform(self._inverse, self._forward)

#-----------------------------------------------------------------------------#
# Power axis scale
#-----------------------------------------------------------------------------#
class PowerScale(mscale.ScaleBase):
    r"""
    Returns a "power scale" that performs the transformation

    .. math::

        x^{c}

    """
    name = 'power'
    """The registered scale name."""
    def __init__(self,
        axis, power=1, inverse=False, *, minpos=1e-300,
        **kwargs):
        """
        Parameters
        ----------
        axis : `~matplotlib.axis.Axis`
            The axis, required for compatibility reasons.
        power : float, optional
            The power :math:`c` to which :math:`x` is raised.
        inverse : bool, optional
            If ``True``, the "forward" direction performs
            the inverse operation :math:`x^{1/c}`.
        minpos : float, optional
            The minimum permissible value, used to truncate negative values.
        """
        super().__init__(axis)
        if not inverse:
            transform = PowerTransform(power, minpos)
        else:
            transform = InvertedPowerTransform(power, minpos)
        self._transform = transform
    def limit_range_for_scale(self, vmin, vmax, minpos):
        return max(vmin, minpos), max(vmax, minpos)
    def set_default_locators_and_formatters(self, axis):
        axis.set_smart_bounds(True) # unnecessary?
        axis.set_major_formatter(Formatter('default'))
        axis.set_minor_formatter(Formatter('null'))
    def get_transform(self):
        return self._transform

class PowerTransform(mtransforms.Transform):
    input_dims = 1
    output_dims = 1
    has_inverse = True
    is_separable = True
    def __init__(self, power, minpos):
        super().__init__()
        self.minpos = minpos
        self._power = power
    def transform(self, a):
        aa = np.array(a).copy()
        aa[aa <= self.minpos] = self.minpos # necessary
        return np.power(np.array(a), self._power)
    def transform_non_affine(self, a):
        return self.transform(a)
    def inverted(self):
        return InvertedPowerTransform(self._power, self.minpos)

class InvertedPowerTransform(mtransforms.Transform):
    input_dims = 1
    output_dims = 1
    has_inverse = True
    is_separable = True
    def __init__(self, power, minpos):
        super().__init__()
        self.minpos = minpos
        self._power = power
    def transform(self, a):
        aa = np.array(a).copy()
        aa[aa <= self.minpos] = self.minpos # necessary
        return np.power(np.array(a), 1/self._power)
    def transform_non_affine(self, a):
        return self.transform(a)
    def inverted(self):
        return PowerTransform(self._power, self.minpos)

#-----------------------------------------------------------------------------#
# Exp axis scale
#-----------------------------------------------------------------------------#
class ExpScale(mscale.ScaleBase):
    """
    An "exponential scale". When `inverse` is ``False`` (the default), this
    performs the transformation

    .. math::

        Ca^{bx}

    where the constants :math:`a`, :math:`b`, and :math:`C` are set by the
    input (see below). When `inverse` is ``False``, this performs the inverse
    transformation

    .. math::

        (\log_a(x) - \log_a(C))/b

    """
    name = 'exp'
    """The registered scale name."""
    def __init__(self, axis,
        a=np.e, b=1, c=1, inverse=False, minpos=1e-300,
        **kwargs):
        """
        Parameters
        ----------
        axis : `~matplotlib.axis.Axis`
            The axis, required for compatibility reasons.
        a : float, optional
            The base of the exponential, i.e. the :math:`a` in :math:`Ca^{bx}`.
        b : float, optional
            The scale for the exponent, i.e. the :math:`b` in :math:`Ca^{bx}`.
        c : float, optional
            The coefficient of the exponential, i.e. the :math:`C`
            in :math:`Ca^{bx}`.
        minpos : float, optional
            The minimum permissible value, used to truncate negative values.
        inverse : bool, optional
            If ``True``, the "forward" direction performs the inverse operation.
        """
        super().__init__(axis)
        if not inverse:
            transform = ExpTransform(a, b, c, minpos)
        else:
            transform = InvertedExpTransform(a, b, c, minpos)
        self._transform = transform
    def limit_range_for_scale(self, vmin, vmax, minpos):
        return max(vmin, minpos), max(vmax, minpos)
    def set_default_locators_and_formatters(self, axis):
        axis.set_smart_bounds(True) # unnecessary?
        axis.set_major_formatter(Formatter('default'))
        axis.set_minor_formatter(Formatter('null'))
    def get_transform(self):
        return self._transform

class ExpTransform(mtransforms.Transform):
    # Arbitrary exponential function
    input_dims = 1
    output_dims = 1
    has_inverse = True
    is_separable = True
    def __init__(self, a, b, c, minpos):
        super().__init__()
        self.minpos = minpos
        self._a = a
        self._b = b
        self._c = c
    def transform(self, a):
        return self._c*np.power(self._a, self._b*np.array(a))
    def transform_non_affine(self, a):
        return self.transform(a)
    def inverted(self):
        return InvertedExpTransform(self._a, self._b, self._c, self.minpos)

class InvertedExpTransform(mtransforms.Transform):
    # Inverse exponential transform
    input_dims = 1
    output_dims = 1
    has_inverse = True
    is_separable = True
    def __init__(self, a, b, c, minpos):
        super().__init__()
        self.minpos = minpos
        self._a = a
        self._b = b
        self._c = c
    def transform(self, a):
        aa = np.array(a).copy()
        aa[aa <= self.minpos] = self.minpos # necessary
        return np.log(aa/self._c)/(self._b * np.log(self._a))
    def transform_non_affine(self, a):
        return self.transform(a)
    def inverted(self):
        return ExpTransform(self._a, self._b, self._c, self.minpos)

#-----------------------------------------------------------------------------#
# Cutoff axis
#-----------------------------------------------------------------------------#
class CutoffScale(mscale.ScaleBase):
    """Axis scale with arbitrary cutoffs that "accelerate" parts of the
    axis, "decelerate" parts of the axes, or discretely jumps between
    numbers.

    If `upper` is not provided, you have the following two possibilities.

    1. If `scale` is greater than 1, the axis is "accelerated" to the right
       of `lower`.
    2. If `scale` is less than 1, the axis is "decelerated" to the right
       of `lower`.

    If `upper` is provided, you have the following three possibilities.

    1. If `scale` is `numpy.inf`, this puts a cliff between `lower` and
       `upper`. The axis discretely jumps from `lower` to `upper`.
    2. If `scale` is greater than 1, the axis is "accelerated" between `lower`
       and `upper`.
    3. If `scale` is less than 1, the axis is "decelerated" between `lower`
       and `upper`.
    """
    name = 'cutoff'
    """The registered scale name."""
    def __init__(self, axis, scale, lower, upper=None, **kwargs):
        """
        Parameters
        ----------
        axis : `~matplotlib.axis.Axis`
            The matplotlib axis. Required for compatibility reasons.
        scale : float
            Value satisfying ``0 < scale <= numpy.inf``. If `scale` is
            greater than ``1``, values to the right of `lower`, or
            between `lower` and `upper`, are "accelerated". Otherwise, values
            are "decelerated". Infinity represents a discrete jump.
        lower : float
            The first cutoff point.
        upper : float, optional
            The second cutoff point (optional, see above).

        Todo
        ----
        Create method for drawing those diagonal "cutoff" strokes with
        whitespace between. See `this post <https://stackoverflow.com/a/5669301/4970632>`__
        for a multi-axis solution and for this class-based solution.
        """
        # Note the space between 1-9 in Paul's answer is because actual
        # cutoffs were 0.1 away (and tick locations are 0.2 apart).
        if scale < 0:
            raise ValueError('Scale must be a positive float.')
        if upper is None and scale == np.inf:
            raise ValueError('For a discrete jump, need both lower and upper bounds. You just provided lower bounds.')
        super().__init__(axis)
        self._transform = CutoffTransform(scale, lower, upper)
    def get_transform(self):
        return self._transform
    def set_default_locators_and_formatters(self, axis):
        # TODO: add example to bug list, smart bounds screws up ticking!
        # axis.set_smart_bounds(True) # may prevent ticks from extending off sides
        axis.set_major_formatter(Formatter('default'))
        axis.set_minor_formatter(Formatter('null'))

class CutoffTransform(mtransforms.Transform):
    # Create transform object
    input_dims = 1
    output_dims = 1
    has_inverse = True
    is_separable = True
    def __init__(self, scale, lower, upper=None):
        self._scale = scale
        self._lower = lower
        self._upper = upper
        super().__init__()
    def transform(self, a):
        a = np.array(a) # very numpy array
        aa = a.copy()
        scale = self._scale
        lower = self._lower
        upper = self._upper
        if upper is None: # just scale between 2 segments
            m = (a > lower)
            aa[m] = a[m] - (a[m] - lower)*(1 - 1/scale)
        elif lower is None:
            m = (a < upper)
            aa[m] = a[m] - (upper - a[m])*(1 - 1/scale)
        else:
            m1 = (a > lower)
            m2 = (a > upper)
            m3 = (a > lower) & (a < upper)
            if scale == np.inf:
                aa[m1] = a[m1] - (upper - lower)
                aa[m3] = lower
            else:
                aa[m2] = a[m2] - (upper - lower)*(1 - 1/scale)
                aa[m3] = a[m3] - (a[m3] - lower)*(1 - 1/scale)
        return aa
    def transform_non_affine(self, a):
        return self.transform(a)
    def inverted(self):
        return InvertedCutoffTransform(self._scale, self._lower, self._upper)

class InvertedCutoffTransform(mtransforms.Transform):
    # Inverse of cutoff transform
    input_dims = 1
    output_dims = 1
    has_inverse = True
    is_separable = True
    def __init__(self):
        super().__init__()
    def transform(self, a):
        a = np.array(a)
        aa = a.copy()
        scale = self._scale
        lower = self._lower
        upper = self._upper
        if upper is None:
            m = (a > lower)
            aa[m] = a[m] + (a[m] - lower)*(1 - 1/scale)
        elif lower is None:
            m = (a < upper)
            aa[m] = a[m] + (upper - a[m])*(1 - 1/scale)
        else:
            n = (upper-lower)*(1 - 1/scale)
            m1 = (a > lower)
            m2 = (a > upper - n)
            m3 = (a > lower) & (a < (upper - n))
            if scale == np.inf:
                aa[m1] = a[m1] + (upper - lower)
            else:
                aa[m2] = a[m2] + n
                aa[m3] = a[m3] + (a[m3] - lower)*(1 - 1/scale)
        return aa
    def transform_non_affine(self, a):
        return self.transform(a)
    def inverted(self):
        return CutoffTransform(self._scale, self._lower, self._upper)

#-----------------------------------------------------------------------------#
# Cartographic scales
#-----------------------------------------------------------------------------#
class MercatorLatitudeScale(mscale.ScaleBase):
    r"""
    Scales axis as with latitude in the `Mercator projection
    <http://en.wikipedia.org/wiki/Mercator_projection>`__. Adapted from `this
    example <https://matplotlib.org/examples/api/custom_scale_example.html>`__.

    The scale function is as follows.

    .. math::

        y = \ln(\tan(\pi x/180) + \sec(\pi x/180))

    The inverse scale function is as follows.

    .. math::

        x = 180\arctan(\sinh(y))/\pi

    """
    name = 'mercator'
    """The registered scale name."""
    def __init__(self, axis, *, thresh=85.0):
        """
        Parameters
        ----------
        axis : `~matplotlib.axis.Axis`
            The matplotlib axis. Required for compatibility reasons.
        thresh : float, optional
            Threshold between 0 and 90, used to constrain axis limits between
            ``-thresh`` and ``+thresh``.
        """
        super().__init__(axis)
        if thresh >= 90.0:
            raise ValueError('Threshold "thresh" must be <=90.')
        self.thresh = thresh
    def get_transform(self):
        return MercatorLatitudeTransform(self.thresh)
    def limit_range_for_scale(self, vmin, vmax, minpos):
        return max(vmin, -self.thresh), min(vmax, self.thresh)
    def set_default_locators_and_formatters(self, axis):
        axis.set_smart_bounds(True)
        axis.set_major_formatter(Formatter('deg'))
        axis.set_minor_formatter(Formatter('null'))

class MercatorLatitudeTransform(mtransforms.Transform):
    # Default attributes
    input_dims = 1
    output_dims = 1
    is_separable = True
    has_inverse = True
    def __init__(self, thresh):
        super().__init__()
        self.thresh = thresh
    def transform_non_affine(self, a):
        # With safeguards
        # TODO: Can improve this?
        a = np.deg2rad(a) # convert to radians
        m = ma.masked_where((a < -self.thresh) | (a > self.thresh), a)
        if m.mask.any():
            return ma.log(np.abs(ma.tan(m) + 1/ma.cos(m)))
        else:
            return np.log(np.abs(np.tan(a) + 1/np.cos(a)))
    def inverted(self):
        return InvertedMercatorLatitudeTransform(self.thresh)

class InvertedMercatorLatitudeTransform(mtransforms.Transform):
    # As above, but for the inverse transform
    input_dims = 1
    output_dims = 1
    is_separable = True
    has_inverse = True
    def __init__(self, thresh):
        super().__init__()
        self.thresh = thresh
    def transform_non_affine(self, a):
        # m = ma.masked_where((a < -self.thresh) | (a > self.thresh), a)
        return np.rad2deg(np.arctan2(1, np.sinh(a))) # always assume in first/fourth quadrant, i.e. go from -pi/2 to pi/2
    def inverted(self):
        return MercatorLatitudeTransform(self.thresh)

class SineLatitudeScale(mscale.ScaleBase):
    r"""
    Scales axis to be linear in the *sine* of *x* in degrees.
    The scale function is as follows.

    .. math::

        y = \sin(\pi x/180)

    The inverse scale function is as follows.

    .. math::

        x = 180\arcsin(y)/\pi
    """
    name = 'sine'
    """The registered scale name."""
    def __init__(self, axis):
        """
        Parameters
        ----------
        axis : `~matplotlib.axis.Axis`
            The matplotlib axis. Required for compatibility reasons.
        """
        super().__init__(axis)
    def get_transform(self):
        return SineLatitudeTransform()
    def limit_range_for_scale(self, vmin, vmax, minpos):
        return max(vmin, -90), min(vmax, 90)
    def set_default_locators_and_formatters(self, axis):
        axis.set_smart_bounds(True)
        axis.set_major_formatter(Formatter('deg'))
        axis.set_minor_formatter(Formatter('null'))

class SineLatitudeTransform(mtransforms.Transform):
    # Default attributes
    input_dims = 1
    output_dims = 1
    is_separable = True
    has_inverse = True
    def __init__(self):
        # Initialize, declare attribute
        super().__init__()
    def transform_non_affine(self, a):
        # With safeguards
        # TODO: Can improve this?
        with np.errstate(invalid='ignore'): # NaNs will always be False
            m = (a >= -90) & (a <= 90)
        if not m.all():
            aa = ma.masked_where(~m, a)
            return ma.sin(np.deg2rad(aa))
        else:
            return np.sin(np.deg2rad(a))
    def inverted(self):
        return InvertedSineLatitudeTransform()

class InvertedSineLatitudeTransform(mtransforms.Transform):
    # Inverse of SineLatitudeTransform
    input_dims = 1
    output_dims = 1
    is_separable = True
    has_inverse = True
    def __init__(self):
        super().__init__()
    def transform_non_affine(self, a):
        # Clipping, instead of setting invalid
        # NOTE: Using ma.arcsin below caused super weird errors, dun do that
        aa = a.copy()
        return np.rad2deg(np.arcsin(aa))
    def inverted(self):
        return SineLatitudeTransform()

#-----------------------------------------------------------------------------#
# Other transformations
#-----------------------------------------------------------------------------#
class InverseScale(mscale.ScaleBase):
    r"""
    Scales axis to be linear in the *inverse* of *x*. The scale
    function and inverse scale function are as follows.

    .. math::

        y = x^{-1}

    """
    # Developer notes:
    # Unlike log-scale, we can't just warp the space between
    # the axis limits -- have to actually change axis limits. Also this
    # scale will invert and swap the limits you provide. Weird! But works great!
    # Declare name
    name = 'inverse'
    """The registered scale name."""
    def __init__(self, axis, minpos=1e-300, **kwargs):
        """
        Parameters
        ----------
        axis : `~matplotlib.axis.Axis`
            The matplotlib axis. Required for compatibility reasons.
        minpos : float, optional
            The minimum permissible value, used to truncate negative values.
        """
        super().__init__(axis)
        self.minpos = minpos
    def get_transform(self):
        return InverseTransform(self.minpos)
    def limit_range_for_scale(self, vmin, vmax, minpos):
        return max(vmin, minpos), max(vmax, minpos)
    def set_default_locators_and_formatters(self, axis):
        # TODO: Fix minor locator issue
        # NOTE: Log formatter can ignore certain major ticks! Why is that?
        axis.set_smart_bounds(True) # may prevent ticks from extending off sides
        axis.set_major_locator(mticker.LogLocator(base=10, subs=(1, 2, 5)))
        axis.set_minor_locator(mticker.LogLocator(base=10, subs='auto'))
        axis.set_major_formatter(Formatter('default')) # use 'log' instead?
        axis.set_minor_formatter(Formatter('null')) # use 'minorlog' instead?

class InverseTransform(mtransforms.Transform):
    # Create transform object
    input_dims = 1
    output_dims = 1
    is_separable = True
    has_inverse = True
    def __init__(self, minpos):
        super().__init__()
        self.minpos = minpos
    def transform(self, a):
        a = np.array(a)
        aa = a.copy()
        # f = np.abs(a) <= self.minpos # attempt for negative-friendly
        # aa[f] = np.sign(a[f])*self.minpos
        aa[aa <= self.minpos] = self.minpos
        return 1.0/aa
    def transform_non_affine(self, a):
        return self.transform(a)
    def inverted(self):
        return InverseTransform(self.minpos)

#-----------------------------------------------------------------------------#
# Declare dictionaries
# Includes some custom classes, so has to go at end
#-----------------------------------------------------------------------------#
scales = mscale._scale_mapping
"""The registered scale names and their associated
`~matplotlib.scale.ScaleBase` classes. See `Scale` for a table."""

locators = {
    'none':        mticker.NullLocator,
    'null':        mticker.NullLocator,
    'auto':        mticker.AutoLocator,
    'log':         mticker.LogLocator,
    'maxn':        mticker.MaxNLocator,
    'linear':      mticker.LinearLocator,
    'multiple':    mticker.MultipleLocator,
    'fixed':       mticker.FixedLocator,
    'index':       mticker.IndexLocator,
    'symmetric':   mticker.SymmetricalLogLocator,
    'logit':       mticker.LogitLocator,
    'minor':       mticker.AutoMinorLocator,
    'date':        mdates.AutoDateLocator,
    'microsecond': mdates.MicrosecondLocator,
    'second':      mdates.SecondLocator,
    'minute':      mdates.MinuteLocator,
    'hour':        mdates.HourLocator,
    'day':         mdates.DayLocator,
    'weekday':     mdates.WeekdayLocator,
    'month':       mdates.MonthLocator,
    'year':        mdates.YearLocator,
    }
"""Mapping of strings to `~matplotlib.ticker.Locator` classes. See
`Locator` for a table."""

formatters = { # note default LogFormatter uses ugly e+00 notation
    'default':    AutoFormatter,
    'auto':       AutoFormatter,
    'frac':       FracFormatter,
    'simple':     SimpleFormatter,
    'date':       mdates.AutoDateFormatter,
    'datestr':    mdates.DateFormatter,
    'scalar':     mticker.ScalarFormatter,
    'none':       mticker.NullFormatter,
    'null':       mticker.NullFormatter,
    'strmethod':  mticker.StrMethodFormatter,
    'formatstr':  mticker.FormatStrFormatter,
    'log':        mticker.LogFormatterSciNotation,
    'sci':        mticker.LogFormatterSciNotation,
    'math':       mticker.LogFormatterMathtext,
    'logit':      mticker.LogitFormatter,
    'eng':        mticker.EngFormatter,
    'percent':    mticker.PercentFormatter,
    'index':      mticker.IndexFormatter,
    }
"""Mapping of strings to `~matplotlib.ticker.Formatter` classes. See
`Formatter` for a table."""
if hasattr(mdates, 'ConciseDateFormatter'):
    formatters['concise'] = mdates.ConciseDateFormatter
if hasattr(mproj, 'ThetaFormatter'):
    formatters['theta'] = mproj.ThetaFormatter

# Monkey patch
# Force scale_factory to accept ScaleBase instances, so that set_xscale and
# set_yscale can accept scales returned by the Scale constructor
if mscale.scale_factory is not _scale_factory:
    mscale.scale_factory = _scale_factory

# Custom scales and overrides
mscale.register_scale(CutoffScale)
mscale.register_scale(ExpScale)
mscale.register_scale(LogScale)
mscale.register_scale(FuncScale)
mscale.register_scale(SymmetricalLogScale)
mscale.register_scale(InverseScale)
mscale.register_scale(SineLatitudeScale)
mscale.register_scale(MercatorLatitudeScale)
