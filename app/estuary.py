""" A simple box-model of an estuary-ocean-river system which tracks the
evolution of oxygen, nutrients, and salinity given simple, idealized
scenarios.

Authors:
    Daniel Rothenberg <darothen@mit.edu>
    Evan Howard <ehoward@whoi.edu>

Version: January 18, 2016

"""

from numpy import array, ceil, mean, sin, pi, vstack
from pandas import DataFrame, Index

import matplotlib.pyplot as plt
import seaborn as sns
sns.set(style='ticks', context='talk')


class EstuaryModel(object):

    """ Container class implementing the simple estuary model.

    Parameters
    ----------
    V, S, N, O: floats
        Initial (average) estuary volume [m3], salinity [kg/m3], and molar
        concentration of nitrogen and oxygen [mmol/m3]
    z : float
        Average estuary depth, in m
    tide_func : function
        A function of the argument `t` (again in hours) which yields
        the mass transport due to tidal inflow and outflow in m3/hr.
        By convention, the function should return positive values for
        inflow and negative values for outflow.
    river_flow_rate : float
        Fraction (preferably between 0 and 0.2) of river flow per day
        relative to estuary mean volume. Set to `0` to disable river
        flow
    N_river, O_river : float
        Nitrogen and oxygen concentration in river in mmol m-3
    S_ocean, N_ocean, O_ocean : floats
        Boundary condition concentrations for S, N, O in ocean and upriver
        sources. Because these are concentrations, S is kg/m3, and N and O
        are mmol/m3
    G : float
        Gas exchange rate in m/d, between 1 and 5
    P : float
        System productivity relative to normal conditions (P=1); may vary
        between 0.5 (cloudy) and 2.0 (bloom)

    Attributes
    ----------
    y0 : array of floats
        Model initial conditions, computed from initial state species
        concentrations
    V0 : float
        Initial estuary volume, in m3
    estuary_area : float
        Surface area of estuary available for gas exchange, based on
        initial geometry (volume / depth) in m3
    has_river, has_tides : boolean
        Flags indicating whether the simulation has river flow and tides,
        respectively

    """

    def __init__(self, V, S, N, O,
                 z=5., tide_func=lambda t: 0,
                 river_flow_rate=0.05, N_river=100., O_river=231.2,
                 S_ocean=35., N_ocean=20., O_ocean=231.2,
                 G=3., P=1.):

        # Bind initial conditions
        self.V = V
        self.S = S
        self.N = N
        self.O = O

        # Bind model parameters and arguments
        self.tide_func = tide_func
        self.z = z

        self.river_flow_rate = river_flow_rate
        self.N_river = N_river
        self.O_river = O_river

        self.S_ocean = S_ocean
        self.N_ocean = N_ocean
        self.O_ocean = O_ocean

        self.G = G
        self.P = P

        # Infer additional parameters
        self.y0 = array([V, S*V, N*V, O*V])
        self.V0 = V
        self.estuary_area = V/z
        self.has_river = river_flow_rate > 0
        self.has_tides = tide_func(1.15) != tide_func(1.85)

    def __call__(self, y, t, *args, **kwargs):
        """ Alias to call the model system of ODEs directly. """
        return self.model_ode(y, t, *args, **kwargs)

    def estuary_ode(self, y, t, P_scale=1.0):
        """ Model system of ODEs.

        This function evaluates the model differential equations
        at a time instant `t`, and returns the vector representing
        the derivative of the model state with respect to time.

        Parameters
        ----------
        y : array
            The current volume, salinity, nitrogen, and ocean state
            variables:
                - V: m3
                - S: kg
                - N: mmol
                - O: mmol
        t : float
            The current evaluation time, in hours.
        P_scale : float
            Factor to scale system productivity,

        Returns
        -------
        dy_dt : array
            Derivative of the current state-time.

        """

        # Un-pack current state
        V, S, N, O = y[:]

        # Pre-compute terms which will be used in the derivative
        # calculations

        # 2) Biological production minus respiration
        # Note: there's clearly some sort of stoichiometry going on here, o
        #       need to find out what those reactions are. also, in Evan's
        #       production code (post-spin-up), this is scaled by the mean
        #       N value from the past 24 hours divided by the ocean N
        #       levels
        J = P_scale*self.P*(125.*16./154.)*sin(2.*pi*(t+0.75)/24. + pi) # mmol/m2/day
        # J /= 24 # day-1 -> h-1

        # 4) Current molar concentrations of N and O (to mmol / m3)
        S = S/V
        N = N/V
        O = O/V

        # 5) Tidal source gradients, given direction of tide
        tidal_flow = self.estuary_area*self.tide_func(t)
        if tidal_flow > 0:
            tidal_S_contrib = tidal_flow*self.S_ocean
            tidal_N_contrib = tidal_flow*self.N_ocean
            tidal_O_contrib = tidal_flow*self.O_ocean
        else:
            # N/O are already in molar concentrations
            tidal_S_contrib = tidal_flow*S
            tidal_N_contrib = tidal_flow*N
            tidal_O_contrib = tidal_flow*O

        # Compute derivative terms
        dV_dt = tidal_flow

        dS_dt = -self.river_flow_rate*self.V0*S + tidal_S_contrib

        dN_dt = -J*self.estuary_area \
              - self.river_flow_rate*self.V0*(N - self.N_river) \
              + tidal_N_contrib

        dO_dt = J*(154./16.)*self.estuary_area \
              + (self.G/24.)*(self.O_river - O)*self.estuary_area \
              - self.river_flow_rate*self.V0*(O - self.O_river) \
              + tidal_O_contrib

        return array([dV_dt, dS_dt, dN_dt, dO_dt])

    def run_model(self, dt=1., t_end=1000., t_spinup=48.):
        """ Run the current model with a simple Euler marching algorithm

        Parameters
        ----------
        dt : float
            Timestep, in hours
        t_end : float
            Cut-off time in hours to end integration/marching
        t_spinup : float
            Time in hours after which productivity will be scaled by
            daily averages of nutrient availability

        Returns
        -------
        result : DataFrame
            A DataFrame with the columns V, S, N, O corresponding to the
            components of the model state vector, indexed along time in hours.
            S, N, O are in kg/m3 and mmol/m3, and V is % of initial volume

        """

        # Initialize output as an array
        out_y = vstack([self.y0, ])
        ts = [0., ]

        # Main integration loop
        i, t = 1, 0.
        while t < t_end:
            # Pop last state off of stack
            y = out_y[-1].T

            # If we're past spin-up, then average the N concentration over
            # the last 24 hours to scale productivity
            if t > t_spinup:
                n_24hrs = int(ceil(24./dt))
                P_scale = \
                    mean(out_y[-n_24hrs:, 2]/out_y[-n_24hrs:, 0])/self.N_ocean
            else:
                P_scale = 1.

            # Euler step
            t += dt
            new_y = y + dt*self.estuary_ode(y, t, P_scale)

            # Correct non-physical V, S, N, or O (where they're < 0)
            new_y[new_y < 0] = 0.

            # Save output onto stack
            out_y = vstack([out_y, new_y])
            ts.append(t)

            i += 1

        # Shape output into DataFrame
        out = out_y[:]
        ts = array(ts)
        result = DataFrame(data=out, columns=['V', 'S', 'N', 'O'],
                           dtype=float,
                           index=Index(ts, name='time'))

        # Convert to molar concentrations
        result.S /= result.V
        result.N /= result.V
        result.O /= result.V

        # Add tidal height (meters) to output
        result['Z'] = result.V/self.estuary_area

        # Convert volume to percentage relative to initial
        result.V = 100*(result.V - self.V)/self.V

        return result


def basic_tidal_flow(t):
    """ Rate of tidal height change in m/s as a function of time in hours. """
    return 0.5*sin(2.*pi*(t / 12.45))


def quick_plot(results, aspect=4., size=3., palette='Dark2'):
    """ Make a quick 3-panel plot with the results timeseries. """

    colors = sns.cycle(sns.color_palette(palette, 3))

    # Compute figure size based on aspect/size
    fig_width = size*aspect
    fig_height = 3*size

    fig, axs = plt.subplots(3, 1, sharex=True, figsize=(fig_width, fig_height))
    ax_S, ax_N, ax_O = axs

    # Salinity
    # Note that results here is in kg/m3, but assuming STP and density of
    # water = 1000 kg/m3, this is equivalent to g/kg
    ax_S.plot(results.index, results.S, color=next(colors))
    ax_S.set_ylabel("Salinity (g/kg)")

    # Nitrogen
    # Note that results here is in mmol/m3, which is equivalent to micromol/L
    # if we assume STP (1 L = 1000 m3)
    ax_N.plot(results.index, results.N, color=next(colors))
    ax_N.set_ylabel("Nitrate ($\mu$mol/L)")

    # Oxygen
    ax_O.plot(results.index, results.O, color=next(colors))
    ax_O.set_ylabel("Oxygen ($\mu$mol/L)")
    ax_O.set_xlabel("Days")

    for ax in axs:
        ax.set_ylim(0)
        ylims = ax.get_ylim()
        ax.vlines(2, ylims[0], ylims[1], linestyle='dashed', color='k')
        ax.set_xlim(0, results.index[-1])

    sns.despine(fig)

    plt.show()

    return fig, axs
