"""
Project Description:
This program is part of the master thesis of Nico Nachtigall. It contains all functions to plot the column
measurements. The plotting is just for testing purpose.

Author: Nico Nachtigall
created: September 2020
last modified: 20.10.2020
"""

from .helperFunction import helperfunction as hp
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from scipy.stats import gaussian_kde
from bokeh.plotting import figure, output_notebook, show
from bokeh.tile_providers import CARTODBPOSITRON, get_provider
import bokeh.models as bmo
from pyproj import Proj


def plot_day(df_toPlot, df_color, **kwargs):
    """
    Function to plot measurements, one plot per day
    :param df_toPlot:   DataFrame that contains all Dates which should be plotted
                        Req. Columns: 'Date','ID_Spectrometer', 'Hour'
    :param df_color:    DataFrame in which the color for each SiteID is stored to be consistent
                        Req. Columns: 'ID_Spectrometer', 'Color'
    :param kwargs:      optional
        sl:             Boolean, set if lowest points should be visualized (only possible if df_comp not given)
        cl:             String, Name of the column which should be plotted (in df_toPlot)
        cl_comp:        String, Name of the column which should be plotted in comparision (in df_comp)
        df_comp:        DataFrame, set if second plot with comparison data should be plotted
        sharey:         Boolean, set if the y axis should be shared
        gas:            String, 'xch4', 'xco2' and 'xco'

    created by: Nico Nachtigall, September 2020
    last modified: 20.10.2020
    """

    df_reset = df_toPlot.reset_index()
    show = kwargs.get('sl', False)
    column = kwargs.get('cl', 'xch4_ppm')
    column_comp = kwargs.get('cl_comp', column)
    df_comp = kwargs.get('df_comp', None)
    sharey = kwargs.get('sharey', False)
    gas = kwargs.get('gas', 'xch4')

    # group by SiteID
    if df_comp is None:
        for keydate, groupdate in df_reset.groupby('Date'):
            fig, ax = plt.subplots(figsize = (16,6))
            for keysite, groupsite in groupdate.groupby('ID_Spectrometer'):
                groupsite.plot(ax=ax, kind='scatter', x='Hour', y=column, title=keydate, label=keysite,
                               color=df_color['Color'].loc[df_color['ID_Spectrometer'] == groupsite['ID_Spectrometer'].values[0]].values[0])
            if show:
                groupdate.plot(ax=ax, kind='scatter', x='Hour', y=gas+'_fixed_background', color='gray', label='background')
            plt.show()
    else:
        df_comp_reset = df_comp.reset_index().set_index(['Date', 'ID_Spectrometer'])
        for keydate, groupdate in df_reset.groupby('Date'):
            fig, (ax_b, ax_a) = plt.subplots(1,2, figsize = (16,6), sharey = sharey)
            for keysite, groupsite in groupdate.groupby('ID_Spectrometer'):
                groupsite.plot(ax=ax_b, kind='scatter', x='Hour', y=column, title=str(keydate)+' - uncorrected', label=keysite,
                               color=df_color['Color'].loc[df_color['ID_Spectrometer'] == groupsite['ID_Spectrometer'].values[0]].values[0])
            try:
                for keysite, groupsite in df_comp_reset.loc[keydate].groupby(level=0):
                    groupsite = groupsite.reset_index()
                    groupsite.plot(ax=ax_a, kind='scatter', x='Hour', y=column_comp, title=str(keydate)+' - corrected', label=keysite, color=df_color['Color'].loc[df_color['ID_Spectrometer'] == groupsite['ID_Spectrometer'].values[0]].values[0])
                    
            except KeyError as e:
                print(e)
            plt.tight_layout()
            plt.show()



def plot_heat_scatter(df, x_column, y_column, **kwargs):
    """
    Function to plot a heat scatter (color is visualizing the point density)
    :param df:          DataFrame with Data
    :param x_column:    String, column Name one
    :param y_column:    String, column Name two
    :param kwargs:      optional
        x_label:        String
        y_label:        String
        title:          String

    reated by: Nico Nachtigall, September 2020
    last modified: 20.10.2020
    """
    # colored scatter plot
    str_x = kwargs.get('x_label', x_column)
    str_y = kwargs.get('y_label', y_column)
    str_title = kwargs.get('title', '')

    x = df[x_column]
    y = df[y_column]

    r_2 = hp.r2(x, y)
    print('The r2 coefficent between {} and {} is: {:f}'.format(x_column, y_column, r_2))

    # Calculate the point density
    xy = np.vstack([x, y])
    z = gaussian_kde(xy)(xy)

    fig, ax = plt.subplots(figsize=(12, 12))
    ax.scatter(x, y, c=z)
    plt.xlabel(str_x)
    plt.ylabel(str_y)
    plt.title(str_title)
    plt.show()


def plot_bokeh(df, x_column, y_column, **kwargs):
    """
    Function to plot a interactive scatter
    :param df:          DataFrame with Data
    :param x_column:    String, column Name one
    :param y_column:    String, column Name two
    :param kwargs:      optional
        x_label:        String
        y_label:        String
        title:          String

    reated by: Nico Nachtigall, September 2020
    last modified: 20.10.2020
    """
    str_x = kwargs.get('x_label', x_column)
    str_y = kwargs.get('y_label', y_column)
    str_title = kwargs.get('title', '')

    r_2 = hp.r2(df[x_column], df[y_column])
    print('The r2 coefficent between {} and {} is: {:f}'.format(x_column, y_column, r_2))

    output_notebook()
    p = figure()
    tooltips = [('time', '@hour'), ('Date', '@date'), ('windSpd', '@windSpd30m'), ('windDir', '@windDir30m')]
    p.add_tools(bmo.HoverTool(tooltips=tooltips))
    p.scatter(x=x_column, y=y_column, source=df)
    p.xaxis.axis_label = str_x
    p.yaxis.axis_label = str_y
    p.title.text = str_title
    show(p)


def plot_regressionPlot(df, x_column, y_column, **kwargs):
    """
    Function to plot a scatter with regression line
    :param df:          DataFrame with Data
    :param x_column:    String, column Name one
    :param y_column:    String, column Name two
    :param kwargs:      optional
        x_label:        String
        y_label:        String
        title:          String

    reated by: Nico Nachtigall, September 2020
    last modified: 20.10.2020
    """
    str_x = kwargs.get('x_label', x_column)
    str_y = kwargs.get('y_label', y_column)
    str_title = kwargs.get('title', '')

    r_2 = hp.r2(df[x_column], df[y_column])
    print('The r2 coefficent between {} and {} is: {:f}'.format(x_column, y_column, r_2))

    ax, fig = plt.subplots(figsize=(12, 12))
    sns.regplot(x=x_column, y=y_column, data=df, ci=0, color='b', line_kws={"color": "red"})
    plt.xlabel(str_x)
    plt.ylabel(str_y)
    plt.title(str_title)
    plt.show()

def plot_location(df, df_location):
    """
    Function to plot the location of the measurements
    :param df:          DataFrame, containing the measurement information, columns: 'ID_Location'
    :param df_location: DataFrame, containing the coordinates, columns: 'ID_Location', 'Coordinates_Longitude', 'Coordinates_Latitude'

    reated by: Nico Nachtigall, September 2020
    last modified: 20.10.2020
    """
    locationID = df['ID_Location'].unique()
    df_locationUsed = df_location.loc[df_location['ID_Location'].isin(locationID)].copy()
    myProj = Proj(init='epsg:3857')
    lon, lat = myProj(df_locationUsed['Coordinates_Longitude'].values, df_locationUsed['Coordinates_Latitude'].values, inverse=False)
    df_locationUsed['Merc_Long'], df_locationUsed['Merc_Lat'] = myProj(df_locationUsed['Coordinates_Longitude'].values, df_locationUsed['Coordinates_Latitude'].values, inverse=False)

    df_locationUsed.rename(columns={'ID_Location':'ID_Location'}, inplace=True)
    # get unique combinations of SiteID and Location_ID
    df_LocSite = df.groupby(['ID_Location','ID_Spectrometer']).size().reset_index().rename(columns={0:'count'})
    #join the two dataframes such that all nessecary information are located in table
    df_alldata = df_locationUsed.set_index('ID_Location').join(df_LocSite.set_index('ID_Location')['ID_Spectrometer'])

    output_notebook()
    #output_file("tile.html")

    tile_provider = get_provider(CARTODBPOSITRON)

    # range bounds supplied in web mercator coordinates
    p = figure(x_range=(1220000, 1350000), y_range=(6110000, 6150000),
               x_axis_type="mercator", y_axis_type="mercator")
    p.add_tile(tile_provider)

    tooltips = [('ID_Spectrometer','@ID_Spectrometer'),('location ID', '@ID_Location')]

    # Add the HoverTool to the figure
    p.add_tools(bmo.HoverTool(tooltips=tooltips))
    #p.circledd(x=lon, y=lat, size=15, fill_color="blue", fill_alpha=0.8)

    p.circle(x='Merc_Long', y='Merc_Lat', size=15, fill_color="blue", fill_alpha=0.8, source=df_alldata)
    show(p)


def plot_windrose(df, column, title, **kwargs):
    """
    Function to plot data in correlation with wind direction and wind speed
    :param df:      Pandas DataFrame, columns: 'windSpd30m', 'windDir30m', column, opt. compare
    :param column:  String, name the column which values should be plotted
    :param title:   String, title of the plot
    :param kwargs:  optional
        compare:    String, name of a column which should be plotted in comparison to column
        ax:         used by function plot_mult_windrose()
        fig:        used by function plot_mult_windrose()
        c_max:      Number, limit color, to get the same colorbar for multiple plots

    created by: Nico Nachtigall, September 2020
    last modified: 20.10.2020
    """
    # set style
    sns.set(style="whitegrid", font_scale=1.5)
    # get input
    compare = kwargs.get('compare', None)  # 'count' or column name
    ax = kwargs.get('ax', None)
    fig = kwargs.get('fig', None)
    color_max = kwargs.get('c_max', None)

    if (compare is not None) & (compare != 'count'):
        df_wind = df[['windSpd30m', 'windDir30m', column, compare]].copy().dropna()
    else:
        subtitle = 'Number of Measurement Points'
        df_wind = df[['windSpd30m', 'windDir30m', column]].copy().dropna()

    df_wind['windDir30m_rad'] = np.radians(df_wind['windDir30m'].values)

    vmin = df_wind['windSpd30m'].min()
    vmax = df_wind['windSpd30m'].max()

    theta = np.linspace(0, 2 * np.pi)
    # r = np.linspace(vmin, vmax, 9)
    r = np.linspace(0, 8, 9)
    Theta, R = np.meshgrid(theta, r)

    np_wsord_index = np.digitize(df_wind['windSpd30m'].values, r) - 1
    np_wdord_index = np.digitize(df_wind['windDir30m_rad'].values, theta) - 1

    df_wind['windSpd30m'] = r[np_wsord_index]
    df_wind['windDir30m_rad'] = theta[np_wdord_index]

    df_windclu = df_wind.groupby(['windSpd30m', 'windDir30m_rad'], as_index=False).mean()

    if compare == 'count':
        df_windclu['count'] = df_wind.groupby(['windSpd30m', 'windDir30m_rad'], as_index=False).count()['windDir30m']
        np_windval = df_windclu[['windSpd30m', 'windDir30m_rad', column, 'count']].values
    elif compare is not None:
        np_windval = df_windclu[['windSpd30m', 'windDir30m_rad', column, compare]].values
    else:
        np_windval = df_windclu[['windSpd30m', 'windDir30m_rad', column]].values

    r_index = []
    theta_index = []
    for i in np_windval[:, 0]:
        r_index = np.append(r_index, np.argwhere(R[:, 0] == i))

    for j in np_windval[:, 1]:
        theta_index = np.append(theta_index, np.argwhere(Theta[0, :] == j))

    np_sorteddata = np.zeros(np.shape(R))
    np_sorteddata[r_index.astype(int), theta_index.astype(int)] = np_windval[:, 2]
    np_sorteddata = np.ma.masked_equal(np_sorteddata, 0)

    if compare is not None:
        np_sortedcompare = np.zeros(np.shape(R))
        np_sortedcompare[r_index.astype(int), theta_index.astype(int)] = np_windval[:, 3]
        np_sortedcompare = np.ma.masked_equal(np_sortedcompare, 0)

    # Plotting
    if compare is None:
        flag = 0
        if (ax is None) or (fig is None):
            fig, ax = plt.subplots(subplot_kw={"projection": "polar"}, figsize=(15, 8))
            flag = 1
        cf = ax.pcolormesh(Theta, R, np_sorteddata, cmap='YlOrRd')
        ax.set_theta_zero_location("N")
        ax.set_theta_direction(-1)
        ax.set_title(title)
        ax.set_rlabel_position(10)
        ax.grid()
        if flag:
            fig.colorbar(cf, ax=ax, orientation='vertical', fraction=0.05, aspect=50, label='Enhancements in ppm')
            plt.tight_layout()
            plt.show()
            return
        return cf

    fig, (ax1, ax2) = plt.subplots(1, 2, subplot_kw={"projection": "polar"}, figsize=(15, 8))
    ax1.set_theta_zero_location("N")
    ax1.set_theta_direction(-1)
    ax1.set_title('Measured Concentration')
    if color_max is None:
        cf = ax1.pcolormesh(Theta, R, np_sorteddata, cmap='YlOrRd')
    else:
        cf = ax1.pcolormesh(Theta, R, np_sorteddata, vmax=color_max, cmap='YlOrRd')
    fig.colorbar(cf, ax=ax1)

    ax2.set_theta_zero_location("N")
    ax2.set_theta_direction(-1)

    if compare == 'count':
        compareTitle = 'Number of Measured Points'
        cf2 = ax2.pcolormesh(Theta, R, np_sortedcompare, vmax=50, cmap='Greens')
    else:
        compareTitle = compare
        cf2 = ax2.pcolormesh(Theta, R, np_sortedcompare, cmap='YlOrRd')

    ax1.set_rlabel_position(10)
    ax2.set_rlabel_position(10)
    ax2.set_title(compareTitle)

    fig.colorbar(cf2, ax=ax2)

    fig.suptitle('Windrose -' + title)
    # plt.savefig('WindRose_allData')
    plt.tight_layout()
    plt.show()

def plot_mult_windrose(df, df2, column, title, df3=None, c_max=None):
    """
    Function to plot multiple windroses with plot_windrose()
    :param df:      Pandas DataFrame, contains information of the first windrose
    :param df2:     Pandas DataFrame, contains information of the first windrose
    :param column:  String, column to be plotted
    :param title:   String
    :param df3:     optional, Pandas DataFrame for third windrose
    :param c_max:   optional, Number to limit colorbar

    created by: Nico Nachtigall, September 2020
    last modified: 20.10.2020
    """
    if df3 is None:
        fig, (ax1, ax2) = plt.subplots(1, 2, subplot_kw={"projection": "polar"}, figsize=(15, 8))
        cf = plot_windrose(df, column, title, ax=ax1, fig=fig, c_max=c_max)
        fig.colorbar(cf, ax=ax1, fraction=0.046, pad=0.04)
        cf = plot_windrose(df2, column, title, ax=ax2, fig=fig, c_max=c_max)
        fig.colorbar(cf, ax=ax2, fraction=0.046, pad=0.04)
        fig.suptitle('Windrose -' + title)
        plt.tight_layout()
        plt.show()
    else:
        fig, (ax1, ax2, ax3) = plt.subplots(1, 3, subplot_kw={"projection": "polar"}, figsize=(25, 8))
        cf = plot_windrose(df, column, title[1], ax=ax1, fig=fig, c_max=c_max)
        fig.colorbar(cf, ax=ax1, fraction=0.046, pad=0.04)
        cf = plot_windrose(df2, column, title[2], ax=ax2, fig=fig, c_max=c_max)
        fig.colorbar(cf, ax=ax2, fraction=0.046, pad=0.04)
        cf = plot_windrose(df3, column, title[3], ax=ax3, fig=fig, c_max=c_max)
        fig.colorbar(cf, ax=ax3, fraction=0.046, pad=0.04)
        fig.suptitle(title[0], fontsize=16)
        fig.tight_layout()
        fig.subplots_adjust(top=0.88)

