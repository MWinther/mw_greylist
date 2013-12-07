#mw-greylist

This is a greylisting plugin for postfix. It uses plug-ins for the different tests, and keeps tab of its data using SQLalchemy. It provides a config file for customization of behavior, and it's in dire need of more documentation.

I am currently using this on my postfix server 2.8.9, and have done little to no testing on older versions. I am also using SQLAlchemy 0.7.6 on top of a postgresql server to keep the data in, although it should work with any compatible SQL server.

To use, simply add a policy entry to your master.cf file, looking something like this:

<pre>policy-mw       unix -  n       n       -       -       spawn
        user=nobody argv=/usr/bin/python /usr/local/bin/mw_greylist/greylist.py</pre>
