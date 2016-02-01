#!/usr/bin/env python
""" Quick run Estuary model """

import matplotlib.pyplot as plt
from app.estuary import EstuaryModel, basic_tidal_flow, quick_plot

model = EstuaryModel(1e9, 35., 20., 231.2,
                     #tide_func=basic_tidal_flow,
                     )
result = model.run_model()

# Convert index from hours to days
result.index = result.index/24.

fig, axs = quick_plot(result, aspect=4.)
