#!/usr/bin/env python
""" Interactive Estuary model app in Bokeh.

"""
import sys
sys.path.append(".")

from numpy import arange
from pandas import DataFrame, Index

from copy import copy
from estuary import EstuaryModel, basic_tidal_flow

from bokeh.io import curdoc
from bokeh.models import ColumnDataSource, Range1d, LinearAxis, CustomJS
from bokeh.models import BoxAnnotation, VBox, HBox, Slider, Toggle, Button
from bokeh.models import DataTable, TableColumn
from bokeh.plotting import Figure

# Default model settings - can be made accessible to user!
model_kwargs = dict(V=1e9, z=5., S_ocean=35., N_ocean=20.,
                    O_ocean=231.2, O_river=231.2,
                    S0=35., N0=20., O0=231.2)
model_run_kwargs = dict(dt=1.0, t_end=24*42.)
colors = [
    'MediumSeaGreen', 'OrangeRed', 'DarkViolet'
]
label_fontsize = "10pt"
tools = "xwheel_zoom,xpan,reset"
day_range = Range1d(0, model_run_kwargs['t_end']/24.)

# Hardcoded constants
SPINUP_DAYS = 2
HYPO_THRESH = 60.

# Figure sizes/styling
figure_style_kws = dict(
    plot_width=600, plot_height=200, min_border=0
)


def get_timestep_index():
    t_end, dt = model_run_kwargs['t_end'], model_run_kwargs['dt']
    return Index(arange(0., t_end+dt, dt), name='time')


# Callback functions for running the model with different settings and
# plotting results
def run_model(has_tide, river_flow_rate, N_river, G, P):
    """ Alias to quickly run the estuary model """

    kwargs = copy(model_kwargs)
    kwargs.update(dict(
        river_flow_rate=river_flow_rate, N_river=N_river,
        G=G, P=P
    ))
    # Set initial conditions
    for elem in ['S', 'N', 'O']:
        kwargs[elem] = kwargs[elem+'0']
        del kwargs[elem+'0']
    if has_tide:
        kwargs['tide_func'] = basic_tidal_flow

    model = EstuaryModel(**kwargs)
    results = model.run_model(**model_run_kwargs)
    results['day'] = results.index/24.

    return results

########################################################################

# Construct basic plot architecture
results = DataFrame({'day': 1, 'S': 0, 'N': 0, 'O': 0, 'V': 1e9, 'Z': 5.},
                    dtype=float, index=get_timestep_index())
source = ColumnDataSource(results)

# Create a new plot and add a renderer
top = Figure(tools=tools, title=None, x_range=day_range,
             **figure_style_kws)
top.line('day', 'S', source=source,
         line_color=colors[0], line_width=3, line_cap='round')
top.y_range = Range1d(0., 40.)
top.yaxis.axis_label = "Salinity (g/kg)"
top.xaxis.axis_label_text_font_size = label_fontsize
top.yaxis.axis_label_text_font_size = label_fontsize

# overlay volume level chart to salinity
tc = "MediumBlue"  # tide color
tide_range = Range1d(start=0, end=15)
tide_axis = LinearAxis(y_range_name="Z")
tide_axis.axis_label = "Tidal Height (m)"
tide_axis.axis_label_text_color = tc
tide_axis.axis_label_text_font_size = label_fontsize
tide_axis.major_tick_line_color = tc
tide_axis.major_label_text_color = tc
tide_axis.minor_tick_line_alpha = 0.

top.extra_y_ranges = {"Z": tide_range}
top.line('day', 'Z', source=source,
         line_color=tc, line_width=2, line_cap='round')
top.add_layout(tide_axis, "right")

mid = Figure(tools=tools, title=None, x_range=top.x_range,
             toolbar_location=None, **figure_style_kws)
mid.line('day', 'N', source=source,
         line_color=colors[1], line_width=3, line_cap='round')
mid.y_range = Range1d(0., 200.)
mid.yaxis.axis_label = "Nitrate (µmol/L)"
mid.xaxis.axis_label_text_font_size = label_fontsize
mid.yaxis.axis_label_text_font_size = label_fontsize


bot = Figure(tools=tools, title=None, x_range=top.x_range,
             toolbar_location=None, **figure_style_kws)
bot.line('day', 'O', source=source,
         line_color=colors[2], line_width=3, line_cap='round')
bot.y_range = Range1d(0., 1000)
bot.yaxis.axis_label = "Oxygen (µmol/L)"
bot.xaxis.axis_label_text_font_size = label_fontsize
bot.yaxis.axis_label_text_font_size = label_fontsize

# Hypoxic criteria line
bot.line([SPINUP_DAYS, day_range.end], [HYPO_THRESH, HYPO_THRESH],
         color='firebrick', line_width=2, line_dash='dashed')

# Set plot aesthetics
for p in [top, mid, bot]:
    p.xgrid.grid_line_color = None
    p.ygrid.grid_line_alpha = 0.5

    p.xaxis.axis_label = "Day"

    # Add spin-up annotation box
    spin_up_box = BoxAnnotation(plot=p, left=0, right=SPINUP_DAYS,
                                fill_alpha=0.75, fill_color='grey')
    p.renderers.extend([spin_up_box, ])

# Generate multi-panel plot and display
plots = VBox(top, mid, bot,
             width=int(figure_style_kws['plot_width']))
# plots = gridplot([[top,], [mid,], [bot,]])


def update_plots():
    """ Callback function to re-run model with new settings. """
    global results

    has_tide = tide_toggle.active
    river_flow_rate = river_flow_slider.value
    N_river = river_N_slider.value
    G = gas_exchange_slider.value
    P = productivity_slider.value

    results = run_model(has_tide, river_flow_rate, N_river, G, P)

    # Update internal data handler with latest results/model run output
    source.data = dict(V=results['V'], S=results['S'],
                       N=results['N'], O=results['O'],
                       Z=results['Z'],
                       day=results['day'])

    # title_str = "Estuary"
    # comps = []
    # if has_tide:
    #     comps += ['tides']
    # if river_flow_rate > 0:
    #     comps += ['river']
    # extra_str = " with " + " and ".join(comps)
    # top.title = title_str + extra_str

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

toggle_ocean = CustomJS(code="""
    var ocean_group = Snap.select("#ocean_group");
    toggleVis(ocean_group);
""")

toggle_river = CustomJS(args=dict(source=source), code="""
    var flow_rate = cb_obj.get('value');
    var river_group = Snap.select("#river_group");

    if (flow_rate > 0) {
        river_group.attr({
            visibility: 'visible',
        });
    } else {
        river_group.attr({
            visibility: 'hidden',
        });
    }
""")

toggle_gas = CustomJS(args=dict(source=source), code="""
    var ex_rate = cb_obj.get('value');
    var gas_group = Snap.select("#gas_group");

    if (ex_rate > 0) {
        gas_group.attr({
            visibility: 'visible',
        });
    } else {
        gas_group.attr({
            visibility: 'hidden',
        });
    }
""")

check_fish = CustomJS(args=dict(source=source), code="""
    var data = source.get('data');
    console.log(data['S'].slice(-1)[0]);
""")

########################################################################
# Configuration sliders/toggles/buttons

river_flow_slider = Slider(title="River Flow (frac of estuary volume/hour)",
                           value=0.05, start=0., end=0.5, step=0.01,
                           callback=toggle_river)
river_N_slider = Slider(title="River Nitrate level (µmol/L)",
                        value=100., start=0., end=200., step=0.1)
gas_exchange_slider = Slider(title="Gas Exchange Rate (m/day)",
                             value=3, start=1, end=5, step=2,
                             callback=toggle_gas)
productivity_slider = Slider(title="Biological Productivity (factor)",
                             value=1., start=0.5, end=2., step=0.5)

# Potential interactive data table for inclusion
columns = [
    TableColumn(field="day", title="Day"),
    TableColumn(field="S", title="Salinity"),
    TableColumn(field="N", title="Nitrate"),
    TableColumn(field="O", title="Oxygen"),
    TableColumn(field="Z", title="Tidal Height")
]
data_table = DataTable(source=source, columns=columns,
                       width=300, height=600)


def toggle_callback(attr):
    if tide_toggle.active:
        # Checked *after* press
        tide_toggle.label = "Disable Tides"
    else:
        tide_toggle.label = "Enable Tides"
tide_toggle = Toggle(label="Enable Tides", callback=toggle_ocean)
tide_toggle.on_click(toggle_callback)

download_button = Button(label="Download data", callback=download_data)

go_button = Button(label="Run model")#, callback=check_fish)
go_button.on_click(update_plots)


# Set up app layout
prods = VBox(gas_exchange_slider, productivity_slider)
river = VBox(river_flow_slider, river_N_slider)
tide_run = HBox(tide_toggle, download_button, go_button)
all_settings = VBox(prods, river, tide_run,
                    width=400)

# Add to current document
curdoc().add_root(HBox(children=[all_settings, plots]))

