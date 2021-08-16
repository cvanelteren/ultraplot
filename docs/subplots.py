# ---
# jupyter:
#   jupytext:
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.4.2
#   kernelspec:
#     display_name: Python 3 (ipykernel)
#     language: python
#     name: python3
# ---

# %% [raw] raw_mimetype="text/restructuredtext"
# .. _ug_subplots:
#
# Subplots
# ========
#
# %% [raw] raw_mimetype="text/restructuredtext"
# .. _ug_abc:
#
# A-b-c labels
# ------------
#
# ProPlot can quickly add "a-b-c" labels to subplots. This is possible because
# ProPlot assigns a unique `~proplot.axes.Axes.number` to each subplot. The
# subplot number can be conrtrolled by passing a `number` keyword to
# `~proplot.figure.Figure.add_subplot`. Otherwise, the subplot number is
# incremented by 1 each time you call `~proplot.figure.Figure.add_subplot`.
#
# If you draw all of your subplots at once with `~proplot.figure.Figure.subplots`,
# the subplot numbers depend on the input arguments. If you :ref:`passed an array <ug_intro>`,
# the subplot numbers correspond to the numbers in the array. If you used the
# `ncols` and `nrows` keyword arguments, the number order is row-major by default
# but can be switched to column-major by passing ``order='F'``. The number order
# also determines the subplot order in the `~proplot.figure.SubplotGrid` returned
# by `~proplot.ui.subplots`.
#
# To turn on "a-b-c" labels, set :rcraw:`abc` to ``True`` or pass ``abc=True``
# to `~proplot.axes.Axes.format` (see :ref:`the format command <ug_format>`
# for details). To change the label style, set :rcraw:`abc` to e.g. ``'A.'`` or
# pass e.g. ``abc='A.'`` to `~proplot.axes.Axes.format`. You can also modify
# the "a-b-c" label location, weight, and size with the :rcraw:`abc.loc`,
# :rcraw:`abc.weight`, and :rcraw:`abc.size` settings. Also note that if the
# an "a-b-c" label and title are in the same position, they are automatically
# offset away from each other.
#
# .. note::
#
#    "Inner" a-b-c labels and titles are surrounded with a white border when
#    :rcraw:`abc.border` and :rcraw:`title.border` are ``True`` (the default).
#    White boxes can be used instead by setting :rcraw:`abc.bbox` and
#    :rcraw:`title.bbox` to ``True``. These options help labels stand
#    out against plotted content. These "borders" and "boxes"
#    can also be used by passing ``border=True`` or ``bbox=True`` to
#    `~matplotlib.axes.Axes.text`, which ProPlot wraps with
#    `~proplot.axes.text_extras`. See the :ref:`plotting sections <ug_1dplots>`
#    for details on wrapper functions.

# %%
import proplot as pplt
fig, axs = pplt.subplots(ncols=3, nrows=3, space=0, refwidth='10em')
axs.format(
    abc='A.', abcloc='ul',
    xticks='null', yticks='null', facecolor='gray5',
    xlabel='x axis', ylabel='y axis',
    suptitle='A-b-c label offsetting, borders, and boxes',
)
axs[:3].format(abcloc='l', titleloc='l', title='Title')
axs[-3:].format(abcbbox=True)  # also disables abcborder
# axs[:-3].format(abcborder=True)  # this is already the default

# %%
import proplot as pplt
fig, axs = pplt.subplots(nrows=8, ncols=8, refwidth=0.7, space=0)
axs.format(
    abc=True, abcloc='ur',
    xlabel='x axis', ylabel='y axis', xticks=[], yticks=[],
    suptitle='A-b-c label stress test'
)


# %% [raw] raw_mimetype="text/restructuredtext"
# .. _ug_autosize:
#
# Automatic size
# --------------
#
# By default, ProPlot determines the suitable figure size given the
# geometry of the subplot grid and the size of a "reference" subplot.
# This "reference" subplot is specified with the `~proplot.ui.subplots`
# keyword `ref` (default is ``1``, i.e. the subplot in the upper left corner).
# ProPlot can also determine the suitable figure height given a fixed figure
# width, and figure width given a fixed figure height.
#
# The ultimate figure size is controlled by the following
# `~proplot.ui.subplots` keyword arguments:
#
# * `refwidth` and `refheight` set the physical dimensions of the reference subplot
#   (default is :rc:`subplots.refwidth`). If one is specified, the other is calculated
#   to satisfy the subplot aspect ratio `refaspect` (default is ``1``). If both are
#   specified, `refaspect` is ignored. When these keyword arguments are used, the
#   width and height of the figure are both determined automatically.
# * `figwidth` and `figheight` set the physical dimensions of the figure.
#   If one is specified, the other is calculated to satisfy `refaspect`
#   and the subplot spacing. If both are specified, or if the `figsize` parameter
#   is specified, the figure size is fixed and `refaspect` is ignored.
# * `journal` constrains the physical dimensions of the figure to meet requirements
#   for submission to an academic journal. For example, ``journal='nat1'``
#   results in a width suitable for single-column *Nature* figures. See
#   :ref:`this table <journal_table>` for the list of available journal
#   specifications (feel free to add to this table by submitting a pull request).
#
# The below examples show how these keyword arguments affect the figure size.
#
# .. important::
#
#    The automatic figure size algorithm has the following notable properties:
#
#    * For very simple subplot grids (e.g., subplots created with the `ncols` and
#      `nrows` arguments), the arguments `refaspect`, `refwidth`, and `refheight`
#      effectively apply to every subplot in the figure -- not just the reference
#      subplot.
#    * When the reference subplot `aspect ratio
#      <https://matplotlib.org/stable/examples/pylab_examples/equal_aspect_ratio.html>`__
#      has been fixed (e.g., using ``ax.set_aspect(1)``) or is set to ``'equal'`` (as
#      with :ref:`geographic projections <ug_geo>` and `~matplotlib.axes.Axes.imshow`
#      images), the fixed aspect ratio is used and the `~proplot.ui.subplots`
#      `refaspect` parameter is ignored. This is critical for getting the figure
#      size right when working with grids of images and geographic projections.
#    * The physical widths of `~proplot.axes.Axes.colorbar`\ s and
#      `~proplot.axes.Axes.panel`\ s are always preserved during figure resizing.
#      ProPlot specifies their widths in physical units to help avoid colorbars
#      and panels that look "too skinny" or "too fat".

# %%
import proplot as pplt
import numpy as np

# Grid of images (note the square pixels)
state = np.random.RandomState(51423)
colors = np.tile(state.rand(8, 12, 1), (1, 1, 3))
fig, axs = pplt.subplots(ncols=3, nrows=2, refwidth=1.7)
fig.format(suptitle='Auto figure size for grid of images')
for ax in axs:
    ax.imshow(colors)

# Grid of cartopy projections
fig, axs = pplt.subplots(ncols=2, nrows=3, proj='robin')
axs.format(land=True, landcolor='k')
fig.format(suptitle='Auto figure size for grid of cartopy projections')


# %%
import proplot as pplt
pplt.rc.update(grid=False, titleloc='uc', titleweight='bold', titlecolor='red9')

# Change the reference subplot width
suptitle = 'Effect of subplot width on figure size'
for refwidth in ('3cm', '5cm'):
    fig, axs = pplt.subplots(ncols=2, refwidth=refwidth,)
    axs[0].format(title=f'refwidth = {refwidth}', suptitle=suptitle)

# Change the reference subplot aspect ratio
suptitle = 'Effect of subplot aspect ratio on figure size'
for refaspect in (1, 2):
    fig, axs = pplt.subplots(ncols=2, refwidth=1.6, refaspect=refaspect)
    axs[0].format(title=f'refaspect = {refaspect}', suptitle=suptitle)

# Change the reference subplot
suptitle = 'Effect of reference subplot on figure size'
for ref in (1, 2):  # with different width ratios
    fig, axs = pplt.subplots(ncols=3, wratios=(3, 2, 2), ref=ref, refwidth=1.1)
    axs[ref - 1].format(title='reference', suptitle=suptitle)
for ref in (1, 2):  # with complex subplot grid
    fig, axs = pplt.subplots([[1, 2], [1, 3]], refnum=ref, refwidth=1.8)
    axs[ref - 1].format(title='reference', suptitle=suptitle)

pplt.rc.reset()

# %% [raw] raw_mimetype="text/restructuredtext"
# .. _ug_tight:
#
# Automatic spaces
# ----------------
#
# In addition to automatic figure sizing, by default ProPlot applies a *tight layout*
# algorithm to every figure. This algorithm automatically adjusts the space between
# subplot rows and columns and the figure edge to accommodate labels.
# It can be disabled by passing ``tight=False`` to `~proplot.ui.subplots`.
# While matplotlib has `its own tight layout algorithm
# <https://matplotlib.org/stable/tutorials/intermediate/tight_layout_guide.html>`__,
# ProPlot's algorithm may change the figure size to accommodate the correct spacing
# and permits variable spacing between subsequent subplot rows and columns (see the
# new `~proplot.gridspec.GridSpec` class for details).
#
# The tight layout algorithm can also be overridden. When you use any
# of the spacing arguments `left`, `right`, `top`, `bottom`, `wspace`, or
# `hspace`, that value is always respected. For example:
#
# * ``left='2em'`` fixes the left margin width, while the right,
#   bottom, and top margin widths are determined automatically.
# * ``wspace='1em'`` fixes the spaces between subplot columns, while the spaces
#   between subplot rows are determined automatically.
# * ``wspace=('3em', None)`` fixes the space between the first two columns of
#   a three-column plot, while the space between the second two columns is
#   determined automatically.
#
# The below examples demonstrate how the tight layout algorithm permits
# variable spacing between subplot rows and columns.

# %%
import proplot as pplt

# Stress test of the tight layout algorithm
# Add large labels along the edge of one subplot
fig, axs = pplt.subplots(nrows=3, ncols=3, refwidth=1.1, share=False)
axs[1].format(
    xlabel='xlabel\nxlabel',
    ylabel='ylabel\nylabel\nylabel\nylabel'
)
axs.format(
    grid=False,
    toplabels=('Column 1', 'Column 2', 'Column 3'),
    leftlabels=('Row 1', 'Row 2', 'Row 3'),
    suptitle='Tight layout with variable row-column spacing'
)

# %%
import proplot as pplt

# Stress test of the tight layout algorithm
# This time override the algorithm between selected subplot rows/columns
fig, axs = pplt.subplots(
    ncols=4, nrows=3, refwidth=1.1, span=False,
    bottom='5em', right='5em',  # margin spacing overrides
    wspace=(0, 0, None), hspace=(0, None),  # column and row spacing overrides
)
axs.format(
    grid=False,
    xlocator=1, ylocator=1, tickdir='inout',
    xlim=(-1.5, 1.5), ylim=(-1.5, 1.5),
    suptitle='Tight layout with user overrides',
    toplabels=('Column 1', 'Column 2', 'Column 3', 'Column 4'),
    leftlabels=('Row 1', 'Row 2', 'Row 3'),
)
axs[0, :].format(xtickloc='top')
axs[2, :].format(xtickloc='both')
axs[:, 1].format(ytickloc='neither')
axs[:, 2].format(ytickloc='right')
axs[:, 3].format(ytickloc='both')
axs[-1, :].format(xlabel='xlabel', title='Title\nTitle\nTitle')
axs[:, 0].format(ylabel='ylabel')


# %% [raw] raw_mimetype="text/restructuredtext"
# .. _ug_share:
#
# Axis sharing
# ------------
#
# :ref:`Redundant labels <why_redundant>` are a common issue for figures with lots of
# subplots. To address this, `matplotlib.pyplot.subplots` includes the `sharex` and
# `sharey` keyword arguments that permit sharing axis limits, ticks, and tick labels
# between like rows and columns of subplots.
#
# ProPlot builds on this feature by...
#
# #. Supporting automatic sharing of subplots and :ref:`axes panels <ug_panels>`
#    spanning the same rows or columns of the `~proplot.gridspec.GridSpec`. This works
#    for :ref:`aribtrarily complex subplot grids <ug_intro>`. It even works if
#    subplots were generated one-by-one with `~proplot.figure.Figure.add_subplot`
#    rather than `~proplot.figure.Figure.subplots`.
# #. Adding four axis-sharing "levels", controlled by the `sharex` and `sharey`
#    keywords (default is :rc:`subplots.share`). Use the `share` keyword as a
#    shorthand to set both `sharex` and `sharey`. The axis-sharing "levels"
#    are defined as follows:
#
#    * ``share=False`` or ``share=0`` disables axis sharing.
#    * ``share='labels'`` or ``share=1`` automatically shares the axis
#      labels, but nothing else.
#    * ``share='limits'`` or ``share=2`` is the same as ``1``, but also
#      shares the axis limits, axis tick locations, and axis scales.
#    * ``share=True`` or ``share=3`` is the same as ``2``, but also
#      shares the axis tick labels.
#
# #. Adding an option to automatically share labels in the same row or column
#    of the subplot grid, controlled by the `spanx` and `spany` keywords
#    (default is :rc:`subplots.span`). Use the `span` keyword as a shorthand
#    to set both `spanx` and `spany`.
#
# Axis and label sharing works for :ref:`arbitrarily complex subplot grids <ug_intro>`.
# The below examples demonstrate the effect of various axis and label sharing settings
# on the appearance of simple subplot grids.

# %%
import proplot as pplt
import numpy as np
N = 50
M = 40
state = np.random.RandomState(51423)
cycle = pplt.Cycle('grays_r', M, left=0.1, right=0.8)
datas = []
for scale in (1, 3, 7, 0.2):
    data = scale * (state.rand(N, M) - 0.5).cumsum(axis=0)[N // 2:, :]
    datas.append(data)

# Same plot with different sharing and spanning settings
for i, share in enumerate((False, 'labels', 'limits', True)):
    fig, axs = pplt.subplots(
        ncols=4, refaspect=1, refwidth=1.06,
        sharey=share, spanx=i // 2
    )
    for ax, data in zip(axs, datas):
        on = ('off', 'on')[i // 2]
        ax.plot(data, cycle=cycle)
        ax.format(
            suptitle=f'Sharing mode {share!r} (level {i}) with spanning labels {on}',
            grid=False, xlabel='spanning', ylabel='shared'
        )

# %%
import proplot as pplt
import numpy as np
pplt.rc.reset()
pplt.rc.cycle = 'Set3'
state = np.random.RandomState(51423)

# Same plot with and without default sharing settings
titles = ('With redundant labels', 'Without redundant labels')
for b in (False, True):
    fig, axs = pplt.subplots(
        nrows=4, ncols=4, refwidth=1, share=b, span=b,
    )
    for ax in axs:
        ax.plot((state.rand(100, 20) - 0.4).cumsum(axis=0))
    axs.format(
        abc=True, abcloc='ul', suptitle=titles[b],
        xlabel='xlabel', ylabel='ylabel',
        grid=False, xticks=25, yticks=5
    )


# %% [raw] raw_mimetype="text/restructuredtext"
# .. _ug_units:
#
# Physical units
# --------------
#
# ProPlot supports arbitrary *physical units* for controlling the figure
# `figwidth` and `figheight`, the reference subplot `refwidth` and `refheight`,
# the gridspec spacing values `left`, `right`, `bottom`, `top`, `wspace`, and
# `hspace`, and in a few other places, e.g. `~proplot.axes.Axes.panel` and
# `~proplot.axes.Axes.colorbar` widths. This feature is powered by the
# `~proplot.utils.units` function.
#
# If a sizing argument is numeric, the units are inches or points; if it is
# string, the units are converted to inches or points by
# `~proplot.utils.units`. A table of acceptable units is found in the
# `~proplot.utils.units` documentation. They include centimeters,
# millimeters, pixels,
# `em-heights <https://en.wikipedia.org/wiki/Em_(typography)>`__,
# `en-heights <https://en.wikipedia.org/wiki/En_(typography)>`__,
# and `points <https://en.wikipedia.org/wiki/Point_(typography)>`__.

# %%
import proplot as pplt
import numpy as np
with pplt.rc.context(fontsize='12px'):
    fig, axs = pplt.subplots(
        ncols=3, figwidth='15cm', figheight='3in',
        wspace=('10pt', '20pt'), right='10mm',
    )
    cmap = pplt.Colormap('Mono')
    cb = fig.colorbar(
        cmap, loc='b', extend='both', label='colorbar',
        width='2em', extendsize='3em', shrink=0.8,
    )
    pax = axs[2].panel_axes('r', width='5en')
axs.format(
    suptitle='Arguments with arbitrary units',
    xlabel='x axis', ylabel='y axis',
    xlim=(0, 1), ylim=(0, 1),
)
