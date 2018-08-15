#!/usr/bin/env python3

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.ticker as ticker

import datetime

import sys

import peecsolar


def plot_solar(val2plot, start_time=None, end_time=None):
    enphase = peecsolar.EnphaseCacher()

    data = enphase.get_data(start_time, end_time)

    times = []
    enwh = []
    powr = []
    for d in data:
        times.append(d['end_at'])
        enwh.append(d['enwh'])
        powr.append(d['powr'])

    fig, ax = plt.subplots()

    if val2plot == 'enwh':
        plt.plot(times, enwh)
    elif val2plot == 'enwh':
        plt.plot(times, powr)
    else:
        plt.plot(times, powr, color='b')
        ax.set_ylabel('Power', color='b')

        ax2 = ax.twinx()
        ax2.plot(times, enwh, color='r')
        ax2.set_ylabel('Energy', color='r')

    # AutoDateLocator supposedly picks the best date format for the data.
    # Ha, good joke! For a 2-day stretch, it shows "year" for every tic.
    # ax.xaxis.set_major_locator(mdates.AutoDateLocator())

    # Want tics every hour, label every 4 hours, date label once a day.
    # Matplotlib can have major and minor locators and formatters,
    # but doesn't have three levels.
    def by_day_formatter(d, pos=None):
        '''Custom matplotlib formatter.
           Label January ticks as "Jan year", July ticks as merely "July"
           but return a full month year string when locating with the mouse.
        '''
        # Empirically, pos is the X position (in some unkmnown coordinates)
        # when setting up axis tics. However, later, when locating mouse
        # positions, pos is None. So we can use pos to tell the difference
        # between locating and labeling, though this is undocumented
        # and thus unreliable.
        d = mdates.num2date(d)
        # print("by_day_formatter: d =", d, ", pos =", pos)
        if pos == None:
            return d.strftime('%Y-%m')
        if d.hour == 0:
            # It would be nice to show both date and time, but
            # matplotlib isn't smart enough to take the full label
            # into account when sizing the window, so anything before
            # the time gets cut off.
            # return d.strftime('%m-%d  %H:%M')
            # so just show the month-day:
            return d.strftime('%b %d')
        if d.minute == 0 and d.hour % 4 == 0:
            return d.strftime('%H:%M')
        return ''
    formatter = ticker.FuncFormatter(by_day_formatter)

    ax.xaxis.set_major_locator(mdates.HourLocator())
    ax.xaxis.set_major_formatter(formatter)

    '''
    ax.xaxis.set_minor_locator(HourLocator)
    # Don't label the minor tics:
    # ax.xaxis.set_minor_formatter(DateFormatter('%b'))

    ax.autoscale_view(tight=True)

    # How to get matplotlib to makr times only on the hour:
    dayloc = mdates.DayLocator(interval = 1)
    hourloc = mdates.HourLocator(interval = 3)
    day_fmt = mdates.DateFormatter('%m-%d  %H:%M')
    hour_fmt = mdates.DateFormatter('%H:%M')
    ax.xaxis.set_major_locator(dayloc)
    ax.xaxis.set_minor_locator(hourloc)
    # ax.xaxis.set_major_formatter(day_fmt)
    ax.xaxis.set_major_formatter(day_fmt)
    ax.xaxis.set_minor_formatter(hour_fmt)
    '''

    plt.setp(ax.xaxis.get_majorticklabels(), rotation=65)
    plt.setp(ax.xaxis.get_minorticklabels(), rotation=65)

    if start_time:
        when = start_time.strftime("%Y-%m-%d")
    else:
        when = "today"

    if val2plot == 'enwh':
        plt.ylabel('Energy (wH)')
        ax.set_title('PEEC Solar %s: Energy' % when)
    elif val2plot == 'powr':
        plt.ylabel('Power (w)')
        ax.set_title('PEEC Solar %s: Power' % when)
    else:
        ax.set_title('PEEC Solar %s: Power and Energy' % when)

    plt.show()


if __name__ == '__main__':
    val2plot = 'both'
    start_time = None
    end_time = None
    for arg in sys.argv[1:]:
        if arg == 'powr' or arg == 'enwh':
            val2plot = arg
        elif arg == 'yesterday':
            start_time = datetime.datetime.now() - datetime.timedelta(days=1)
            start_time = start_time.replace(hour=0, minute=0,
                                            second=0, microsecond=0)
            end_time = start_time.replace(hour=19, minute=55)
        elif arg.isdigit():
            start_time = datetime.datetime.now() \
                         - datetime.timedelta(days=int(arg))
            start_time = start_time.replace(hour=0, minute=0,
                                            second=0, microsecond=0)
            end_time = datetime.datetime.now()

    plot_solar(val2plot, start_time=start_time, end_time=end_time)
