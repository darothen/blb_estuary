# Estuary Model/App

This is an app designed around a simple model of an estuary-ocean-riverine ecological system for use in the [2016 Blue Lobster Bowl](http://seagrant.mit.edu/blb.php) taking place at MIT in March, 2016. One of the activities at the competition will involve understanding the details of the estuary system using this interactive application. 

The estuary model itself is a simple set of coupled ordinary differential equations which are solved numerically; we use a straightforward explicit marching scheme to eliminate dependencies on external libraries. The app interface to the model is written using [Bokeh](http://bokeh.pydata.org/), an open-source Python visualization toolkit similar to d3.js. 

