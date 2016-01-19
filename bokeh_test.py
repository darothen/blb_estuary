#!/usr/bin/env python

import os

from estuary import EstuaryModel, basic_tidal_flow, quick_plot

from bokeh import mpl
from bokeh.models import ColumnDataSource, Range1d, BoxAnnotation
from bokeh.plotting import figure, gridplot, show, output_file

model = EstuaryModel(1e9, 35., 20., 231.2,
                     tide_func=basic_tidal_flow)
result = model.run_model(dt=0.5)

# Convert index from hours to days
result['day'] = result.index/24.


def rgb_to_hex(rgb):
    """ Convert RGB tuple to hex triplet """
    rgb = tuple([bit*256 for bit in rgb]) # (0,1) -> (0, 256)
    return'#%02x%02x%02x' % rgb


def basic_bokeh(out_fn="estuary_out.html"):
    """ Basic 3-panel plot of output using Bokeh """

    if os.path.exists(out_fn):
        os.remove(out_fn)
    output_file(out_fn)

    # Construct Bokeh plot
    source = ColumnDataSource(result)
    day_range = Range1d(0, result.iloc[-1]['day'])

    # colors = sns.cycle([rgb_to_hex(c) for c in sns.color_palette('Dark2', 3)])
    colors = [
        'MediumSeaGreen', 'OrangeRed', 'DarkViolet'
    ]

    TOOLS = "box_zoom,reset"

    # Create a new plot and add a renderer
    top = figure(tools=TOOLS, width=1000, height=300, title=None,
                 x_range=day_range)
    top.line('day', 'S', source=source,
             line_color=colors[0], line_width=3, line_cap='round')
    top.y_range = Range1d(0, 1.05*result['S'].max())
    top.yaxis.axis_label = "Salinity (g/kg)"

    mid = figure(tools=TOOLS, width=1000, height=300, title=None,
                 x_range=top.x_range)
    mid.line('day', 'N', source=source,
             line_color=colors[1], line_width=3, line_cap='round')
    mid.y_range = Range1d(0, 1.05*result['N'].max())
    mid.yaxis.axis_label = "Nitrate (mu mol/L)"

    bot = figure(tools=TOOLS, width=1000, height=300, title=None,
                 x_range=top.x_range)
    bot.line('day', 'O', source=source,
             line_color=colors[2], line_width=3, line_cap='round')
    bot.y_range = Range1d(0, 1.05*result['O'].max())
    bot.yaxis.axis_label = "Oxygen (mu mol/L)"

    # Set plot aesthetics
    for p in [top, mid, bot]:
        p.xgrid.grid_line_color = None
        p.ygrid.grid_line_alpha = 0.5

        p.xaxis.axis_label = "Day"

        # Add spin-up annotation box
        spin_up_box = BoxAnnotation(plot=p, left=0, right=2,
                                    fill_alpha=0.75, fill_color='grey')
        p.renderers.extend([spin_up_box, ])


    # Generate multi-panel plot and display
    p = gridplot([[top, ], [mid, ], [bot, ]],
                 toolbar_location='above')
    show(p)


def from_quick_plot(out_fn="estuary_out.html"):
    """ Convert matplotlib quick plot to Bokeh """
    fig, _ = quick_plot(result, aspect=4.)
    show(mpl.to_bokeh(fig))