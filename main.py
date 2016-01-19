#!/usr/bin/env python
""" Interactive Estuary model app in Bokeh.

"""
from numpy import arange
from pandas import DataFrame, Index

from copy import copy
from estuary import EstuaryModel, basic_tidal_flow

from bokeh.io import curdoc
from bokeh.models import ColumnDataSource, Range1d, CustomJS
from bokeh.models import BoxAnnotation, VBox, HBox, Slider, Toggle, Button
from bokeh.plotting import Figure

# Default model settings - can be made accessible to user!
model_kwargs = dict(V=1e9, z=5., S_ocean=35., N_ocean=20.,
                    O_ocean=231.2, O_river=231.2)
model_run_kwargs = dict(dt=1.0, t_end=24*42.)
colors = [
    'MediumSeaGreen', 'OrangeRed', 'DarkViolet'
]
tools = "xwheel_zoom,xpan,reset"
day_range = Range1d(0, model_run_kwargs['t_end']/24.)


def get_timestep_index():
    t_end, dt = model_run_kwargs['t_end'], model_run_kwargs['dt']
    return Index(arange(0., t_end+dt, dt), name='time')


# Callback functions for running the model with different settings and
# plotting results
def run_model(S0, N0, O0, has_tide, river_flow_rate, N_river, G, P):
    """ Alias to quickly run the estuary model """

    kwargs = copy(model_kwargs)
    kwargs.update(dict(
        S=S0, N=N0, O=O0, river_flow_rate=river_flow_rate, N_river=N_river,
        G=G, P=P
    ))
    if has_tide:
        kwargs['tide_func'] = basic_tidal_flow

    model = EstuaryModel(**kwargs)
    results = model.run_model(**model_run_kwargs)
    results['day'] = results.index/24.

    return results

########################################################################

# Construct basic plot architecture
results = DataFrame({'day': 1, 'S': 0, 'N': 0, 'O': 0, 'V': 1e9},
                    dtype=float, index=get_timestep_index())
source = ColumnDataSource(results)

# Create a new plot and add a renderer
top = Figure(tools=tools, title=None, x_range=day_range)
top.line('day', 'S', source=source,
         line_color=colors[0], line_width=3, line_cap='round')
top.y_range = Range1d(0., 40.)
top.yaxis.axis_label = "Salinity (g/kg)"

mid = Figure(tools=tools, title=None, x_range=top.x_range,
             toolbar_location=None)
mid.line('day', 'N', source=source,
         line_color=colors[1], line_width=3, line_cap='round')
mid.y_range = Range1d(0., 200.)
mid.yaxis.axis_label = "Nitrate (mu mol/L)"

bot = Figure(tools=tools, title=None, x_range=top.x_range,
             toolbar_location=None)
bot.line('day', 'O', source=source,
         line_color=colors[2], line_width=3, line_cap='round')
bot.y_range = Range1d(0., 1000.)
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
plots = VBox(top, mid, bot)


def update_plots():
    """ Callback function to re-run model with new settings. """
    global results

    S0, N0, O0 = S_init_slider.value, N_init_slider.value, O_init_slider.value
    has_tide = tide_toggle.active
    river_flow_rate = river_flow_slider.value
    N_river = river_N_slider.value
    G = gas_exchange_slider.value
    P = productivity_slider.value

    results = run_model(S0, N0, O0, has_tide, river_flow_rate, N_river, G, P)

    source.data['V'] = results['V']
    source.data['S'] = results['S']
    source.data['N'] = results['N']
    source.data['O'] = results['O']
    source.data['day'] = results['day']

    title_str = "Estuary"
    comps = []
    if has_tide: comps += ['tides']
    if river_flow_rate > 0: comps += ['river']
    extra_str = " with " + " and ".join(comps)
    top.title = title_str + extra_str

    # Reset plot ranges if necessary
    # TODO: This seems to be an open bug in bokeh, where the plot doesn't
    #       detect the need to re-draw following a range change.
    if results['S'].max() > top.y_range.end:
        top.y_range = Range1d(0, 1.05*results['S'].max())
    if results['N'].max() > mid.y_range.end:
        mid.y_range = Range1d(0, 1.05*results['N'].max())
    if results['O'].max() > bot.y_range.end:
        bot.y_range = Range1d(0, 1.05*results['O'].max())


# Callback using Javascript to download current data as a CSV; note that
# I've hardcoded in the iteration over objKeys (since I know the number of
# columns in the source data) but it would have to be changed if the model
# state variables change. This follows the example by Schaun Wheeler,
# https://groups.google.com/a/continuum.io/forum/#!topic/bokeh/jMKf_Acj3XU
download_data = CustomJS(args=dict(objArray=source), code="""

    array = objArray.attributes.data;
    var str = '';
    var line = '';
    objKeys = Object.keys(array);
    var placeholder_key = objKeys[0];

    console.log("Iterating over array to id keys");
    for (i = 0; i < objKeys.length; i++ ) {
        var value = objKeys[i] + "";
        console.log(i, value);
        line += '"' + value.replace(/"/g, '""') + '",';
    }
    line = line.slice(0, -1);
    str += line + '\\r\\n';

    console.log("Iterating again to record all data")
    for (i = 0; i < array[placeholder_key].length; i++) {
        var line = '';
        console.log(i)
        for (j = 0; j < objKeys.length; j++) {
            var index = objKeys[j]
            var value = array[index][i] + "";
            line += '"' + value.replace(/"/g, '""') + '",';
        }
        line = line.slice(0, -1);
        str += line + '\\r\\n';
    }
    console.log("... done!")

    var csv = escape(str);
    window.open("data:text/csv;charset=utf-8," + csv);

""")

########################################################################

# Configuration sliders/toggles/buttons
S_init_slider = Slider(title="Initial S concentration (kg/m3)",
                       value=35., start=0., end=40., step=0.1)
N_init_slider = Slider(title="Initial N concentration (mu mol/L)",
                       value=20., start=0., end=100., step=0.1)
O_init_slider = Slider(title="Initial O concentration (mu mol/L)",
                       value=231.2, start=200., end=300., step=0.1)

river_flow_slider = Slider(title="River Flow (volume fraction/day)",
                           value=0.05, start=0., end=0.5, step=0.01)
river_N_slider = Slider(title="River Nitrate level (mu mol/L)",
                        value=100., start=0., end=200., step=0.1)
gas_exchange_slider = Slider(title="Gas Exchange Rate (m/day)",
                             value=3., start=1., end=5., step=0.1)
productivity_slider = Slider(title="System Productivity (factor)",
                             value=1., start=0.5, end=2., step=0.1)


def toggle_callback(attr):
    if tide_toggle.active: # Checked *after* press
        tide_toggle.label = "Disable tides"
    else:
        tide_toggle.label = "Enable tides"
tide_toggle = Toggle(label="Enable tides")
tide_toggle.on_click(toggle_callback)

download_button = Button(label="Download plot data", callback=download_data)

go_button = Button(label="Run model")
go_button.on_click(update_plots)

# Set up app layout
inits = VBox(S_init_slider, N_init_slider, O_init_slider)
prods = VBox(gas_exchange_slider, productivity_slider)
river = VBox(river_flow_slider, river_N_slider)
tide_run = HBox(tide_toggle, download_button, go_button)
all_settings = VBox(inits, prods, river, tide_run)

# Add to current document
curdoc().add_root(HBox(all_settings, plots, width=1400))
