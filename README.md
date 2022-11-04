# Colorful ICMP pings for your terminal

```
usage: fancyping [-h] [-a] [-A] [-c COUNT] [-f] [-F] [-i INTERVAL] [-q] [-Q] [-t TIMEOUT] [--version] TARGET

Colorful ICMP pings for your terminal

positional arguments:
  TARGET

options:
  -h, --help            show this help message and exit
  -a, --no-up-anim      disable animation while TARGET is up
  -A, --no-down-anim    disable animation while TARGET is down
  -c COUNT, --count COUNT
                        quit after this many pings
  -f, --color-up        fullscreen color while TARGET is up
  -F, --color-down      fullscreen color while TARGET is down
  -i INTERVAL, --interval INTERVAL
                        number of seconds between each ping (defaults to 1)
  -q, --quit-up         quit when TARGET is up
  -Q, --quit-down       quit when TARGET is down
  -t TIMEOUT, --timeout TIMEOUT
                        number of seconds before a ping is considered lost (defaults to 2)
  --version             show program's version number and exit

HOTKEYS

 +/-  change stats interval
  Q   quit
  R   write report to current directory (timestamps at response)
  X   reset stats
```
