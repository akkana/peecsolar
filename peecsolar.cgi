#!/usr/bin/env python3

import json
import csv
import requests
import datetime
import time
import os, sys
import cgi

# While debugging the CGI:
import cgitb
# cgitb.enable()

from cachefile import Cachefile


# https://api.enphaseenergy.com/api/v2/systems/67/summary?key=qbAr1295717

# Keys needed for the Enphase API will be read from ~/.config/enphase.conf
# To get these values:
#   key: sign up for an Enphase API account.
#   user_id: visit the "activation URL" that's shown when you activate the
#     API account. Log in with the credentials for the solar site (not
#     the credentials for the API account) and authorize, then copy
#     the 18-digit user id.
#   system_id: armed with key and user_id, set system_id = None
#     then run get_system_id() below.

class EnphaseCacher(Cachefile):
    def __init__(self, cachedir=None, conffile=None):
        if not cachedir:
            cachedir = "enphase"
        super(EnphaseCacher, self).__init__(cachedir)
        self.verbose = False

        self.TIME = 'end_at'
        self.apikeys = {
            'key': None,
            'user_id': None,
            'system_id': None,
            'user_id': None
        }

        self.get_keys(conffile=conffile)


    def fetch_one_day_data(self, day):
        starttime, endtime = self.time_bounds(day)
        return self.fetch_data(starttime, endtime)

    def fetch_data(self, starttime=None, endtime=None):
        '''Fetch data from the Enphase web API.
        '''

        url = 'https://api.enphaseenergy.com/api/v2/systems/%s/stats?key=%s&user_id=%s' % (self.apikeys['system_id'], self.apikeys['key'], self.apikeys['user_id'])

        # The API wants start and end times (if any) in Unix timestamp.
        if starttime:
            url += '&start_at=%d' % time.mktime(starttime.timetuple())
        if endtime:
            url += '&end_at=%d' % time.mktime(endtime.timetuple())

        if self.verbose:
            print("Fetching", url)
        r = requests.get(url)
        if r.status_code != 200:
            raise RuntimeError("Status code %d: %s" (r.status_code, r.text))
        data = json.loads(r.text)

        # Convert dates (Unix timestamp) to datetime
        try:
            for interval in data['intervals']:
                interval['end_at'] = \
                    datetime.datetime.fromtimestamp(interval['end_at'])

        except Exception as e:
            print("Problem with data:", str(e))
            print("data", data)
            sys.exit(1)

        return data['intervals']


    @staticmethod
    def parse_time(timestr):
        try:
            return datetime.datetime.strptime(timestr, '%Y-%m-%d %H:%M')
        except ValueError:
            pass

        try:
            return datetime.datetime.strptime(timestr, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            pass

        # If those didn't work, and this doesn't either,
        # go ahead and throw a ValueError.
        return datetime.datetime.strptime(timestr, '%Y-%m-%d %H:%M:%S.%f')


    def apply_types(self, row):
        # Given a row that was just read in as strings, change the items
        # to appropriate types, e.g. int, float, datetime etc.
        row[self.TIME] = self.parse_time(row[self.TIME])

        row['powr'] = int(row['powr'])
        row['enwh'] = int(row['enwh'])
        row['devices_reporting'] = int(row['devices_reporting'])


    def get_keys(self, conffile=None):
        if not conffile:
            conffile = os.path.expanduser("~/.config/enphase.conf")
        with open(conffile) as fp:
            for line in fp:
                if not line or line.startswith('#'):
                    continue
                if '=' in line:
                    name, val = [ item.strip()
                                  for item in line.split('=', maxsplit=1) ]
                    self.apikeys[name] = val

        if not self.apikeys['system_id']:
            self.get_system_id()
            if self.verbose:
                print("system_id:", self.apikeys['system_id'])

        if self.verbose:
            print("read keys:", self.apikeys)


    def get_system_id(self):
        '''The enphase documentation gives the wrong URL and doesn't mention
        that you need the system_id, which you can get this way:
        https://developer.enphase.com/forum/topics/not-authorized-to-access-requested-resource
        '''

        url = 'https://api.enphaseenergy.com/api/v2/systems?key=%s&user_id=%s' % (self.apikeys['key'], self.apikeys['user_id'])
        r = requests.get(url)
        data = json.loads(r.text)
        self.apikeys['system_id'] = data['systems'][0]['system_id']


# def get_summary():
#     # This is what their documentation says to use:
#     # url = "https://api.enphaseenergy.com/api/v2/systems/67/summary?key=%s&user_id=%s" % (key, user_id)
#     # but this the real request (see forum post referened in get_system_id()):
#     url = 'https://api.enphaseenergy.com/api/v2/systems/%s/summary?key=%s&user_id=%s' % (self.apikeys['system_id'], self.apikeys['key'], self.apikeys['user_id'])
#     r = requests.get(url)
#     return json.loads(r.text)

# Mode can be either 'csv', 'json' or 'text'
mode = 'csv'


if __name__ == '__main__':

    starttime = None
    endtime = None

    # Are we being called via CGI?
    # There doesn't seem to be any way to tell if there are no form args.
    if True or 'REQUEST_METHOD' in os.environ:
        if mode == 'csv':
            print("Content-type: text/csv\n\nend_at,powr,enwh")
        elif mode == 'json':
            print("Content-type: application/json\n\n[")
        else:
            print("Content-type: text/plain\n")

        form = cgi.FieldStorage()

        conffile = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "enphase.conf")
        cachedir = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "cache")

    else:
        cachedir = None
        conffile = None

    enphase = EnphaseCacher(cachedir, conffile)

    if 'when' in form:
        if form['when'].value == 'yesterday':
            starttime = enphase.day_start(datetime.datetime.now())
            starttime -= datetime.timedelta(days=1)
        elif form['when'].value == 'week':
            starttime = enphase.day_start(datetime.datetime.now())
            starttime -= datetime.timedelta(days=7)

    else:
        if 'start' in form:
            starttime = datetime.datetime.strptime(form['start'].value.strip(),
                                                   '%Y-%m-%d %H:%M')

        if 'end' in form:
            endtime = form['end'].value.strip()

    if not starttime:
        starttime = enphase.day_start(datetime.datetime.now())
    if not endtime:
        endtime = datetime.datetime.now()

    stats = enphase.get_data(starttime, endtime)

    for interval in stats:
        if mode == 'csv':
            print("%s,%d,%d" % (interval['end_at'], interval['powr'],
                                interval['enwh']))
        elif mode == 'json':
            print("{ end_at: %s, powr: %d, enwh: %d ]"
                  % (interval['end_at'],
                     interval['powr'], interval['enwh']))
        else:
            print("%10s  %4d %4d" % (interval['end_at'], interval['powr'],
                                    interval['enwh']))


