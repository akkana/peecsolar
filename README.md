# peecsolar
## Plot output from PEEC's solar panels using the Enphase solar API and Chart.py

This implements a web page that can plot the power or energy history
from Enphase solar panels using Enphase's solar API.

It's written for
[PEEC, the Pajarito Environmental Education Center](http://peecnature.org)
but it should be usable for anyone with an Enphase API account.
Just create a config file called *enphase.conf* either in the same
directory as your web page, or in ~/.config (where ~ is the home directory
of the user who will run the app, possibly the web server's user).
You'll need:
```
key = [32 digit key]
system_id = [7-digit system ID]
user_id = [18-digit user ID]
```

You'll also need a writable cache dir: by default this is set up
to use a directory called *cache* in the same directory as the
web page and CGI script. It must be writable by the web server user.

## About the Code

This repository also serves as an example of how to use Chart.js
to plot data fetched over the web. I had a hard time finding any
useful examples of that.

The web page, solar.html, uses Javascript's *XMLHttpRequest()* to
fetch data from a CGI script. The CGI script, written in Python, uses
[cachefile.py](https://github.com/akkana/scripts/blob/master/cachefile.py)
to keep a local cache of each day's data, since the Enphase API is quite
slow for interactive web use and some accounts may be rate limited.
Copy cachefile.py into the same directory as peecsolar, or put it
anywhere in your (or the web server's) PYTHONPATH.

As noted, this is written for PEEC's specific website and so isn't
designed to be plug-and-play for everybody. However, I hope the code
turns out to be useful for other projects.

There's also a Python script called plotsolar.py. To use it, you need
to link peecsolar.cgi to peecsolar.py so plotsolar.py can import peecsolar.
