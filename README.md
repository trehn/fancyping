# Colorful ICMP pings for your terminal

```
usage: fancyping [-h] [-a] [-A] [-c COUNT] [-f] [-F] [-g HISTOGRAM_UPPER] [-G HISTOGRAM_LINES] [-i INTERVAL] [-l LOSS_TOLERANCE] [-q] [-Q] [-t TIMEOUT] [--version] TARGET

Colorful ICMP pings for your terminal

positional arguments:
  TARGET

options:
  -h, --help            show this help message and exit
  -a, --no-up-anim      disable animation while TARGET is up
  -A, --down-anim       enable animation while TARGET is down
  -c COUNT, --count COUNT
                        quit after this many pings
  -f, --color-up        fullscreen color while TARGET is up
  -F, --no-color-down   disable fullscreen color while TARGET is down
  -g HISTOGRAM_UPPER, --histogram-upper HISTOGRAM_UPPER
                        upper end of histogram scale in ms (defaults to 300)
  -G HISTOGRAM_LINES, --histogram-lines HISTOGRAM_LINES
                        number of lines for the histogram at the bottom (defaults to 3)
  -i INTERVAL, --interval INTERVAL
                        number of seconds between each ping (defaults to 1)
  -l LOSS_TOLERANCE, --loss-tolerance LOSS_TOLERANCE
                        number of consecutive timeouts until TARGET is considered down (defaults to 1)
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
