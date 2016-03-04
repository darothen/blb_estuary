This webapp lets you explore how physics, chemistry, and biology combine in a simple model of an estuary. Behind the scenes, we're running a model to evaluate the state of an idealized esturay, based on settings you provide us with through the buttons and sliders on the top-left part of this page. Based on those settings, the schematic below the sliders will update to indicate what sources and sinks you've included in your simulation.

## Running the Model

You an configure the model inputs and parameters by dragging the sliders above, and you can enable/disable tides using the button underneath the sliders. Here's a quick reference for the parameters we've given you control of:

1. **Enable/Disable tides**: Simulate in/out-flow from tides entering/exiting the estuary, parameterizing as the change in tidal height as a function of time.
2. **Gas Exchange Rate**: The rate at which oxygen in the estuary is exchanged with the atmosphere. The units here can be considered the "depth" of the estuary which would exchange with the air over the course of a day.
3. **Biological Productivity**: This non-dimensional factor controls how "active" the biology in the estuary is, relative to an initial value of "1". Setting this to different levels simulates how some external factors - such as cloudiness or some other parameter not considered in the model - could influence the estuary biology.
4. **River Flow Rate**: What volume of water is entering the estuary from the river. When set to "0", there is no river attached to the estuary system. This flow rate is expressed as the fraction of the total estuary volume which would be replaced by the flowing river each hour.
5. **River Nitrate Level**: The amount of nitrate in the river water flowing into the estuary.

Once you've set the model's conditions, click the "Run Model" button; the plots on the right-hand side above should show the model output for four fields:

1. Salinity
2. Tidal Height
3. Nitrate (nutrient) molar concentration
4. Oxygen molar concentration

We've included two graphical references on the plots. The "gray" box at the beginning of each plot is the model "spin-up" period. During these first two days, we're letting the model reach an equilibrium before we apply your parameter settings. We've grayed out this period so that you're not tempted to interpret some of the weird things that can happen before the model has reached its equilibrium state! Second, we've indicated a threshold for hypoxia (60 µmol/L) on the Oxygen plot. When the curve dips below this threshold, you should investigate!


## Plot Control

Using the tools in the upper-right corner of the top plot, you can investigate the output in more detail. With the tools enabled, hover your mouse over the top plot. Clicking/holding and dragging the mouse left and right will pan the plots forwards and backwards in time. Scrolling the mousewhell will zoom in/out on the date at the center of the plots. Clicking the third button, "reset", will return the plots to their original state.

Finally, if you would like to save the data from the plot, you can do so by clicking on the "Download data" button; this will download the model results in a comma-separated values table, which you can open in Excel to look at and make your own plots.

## Model Code

If you're really interested, you can check out the code for this model [on our archive online](https://github.com/darothen/blb_estuary/tree/master/app). The file `estuary.py` contains the actual estuary model; one level higher in the archive, the script `quick.py` shows how simple it is to setup and run the model. The rest of the files probably aren't interesting to you; they're just code to make the app you're using work.