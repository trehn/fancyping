from argparse import ArgumentParser, RawTextHelpFormatter
from os import environ, getcwd
from sys import argv, exit

from . import VERSION_STRING
from .icmp import PingRecorder
from .ui import run_ui


HOTKEY_HELP = """
HOTKEYS

 +/-  change stats interval
  Q   quit
  R   write report to current directory (timestamps at response)
  X   reset stats
"""


def build_parser():
    parser = ArgumentParser(
        prog="fancyping",
        description="Colorful ICMP pings for your terminal",
        epilog=HOTKEY_HELP,
        formatter_class=RawTextHelpFormatter,
    )
    parser.add_argument(
        'target',
        metavar="TARGET",
        type=str,
    )
    parser.add_argument(
        "-a",
        "--no-up-anim",
        action='store_false',
        dest='anim_up',
        help="disable animation while TARGET is up",
    )
    parser.add_argument(
        "-A",
        "--down-anim",
        action='store_true',
        dest='anim_down',
        help="enable animation while TARGET is down",
    )
    parser.add_argument(
        "-c",
        "--count",
        default=0,
        dest='count',
        help="quit after this many pings",
        type=int,
    )
    parser.add_argument(
        "-f",
        "--color-up",
        action='store_true',
        dest='color_up',
        help="fullscreen color while TARGET is up",
    )
    parser.add_argument(
        "-F",
        "--no-color-down",
        action='store_false',
        dest='color_down',
        help="disable fullscreen color while TARGET is down",
    )
    parser.add_argument(
        "-g",
        "--histogram-upper",
        default=300.0,
        dest='histogram_upper',
        help="upper end of histogram scale in ms (defaults to 300)",
        type=float,
    )
    parser.add_argument(
        "-G",
        "--histogram-lines",
        default=3,
        dest='histogram_lines',
        help="number of lines for the histogram at the bottom (defaults to 3)",
        type=int,
    )
    parser.add_argument(
        "-i",
        "--interval",
        default=1.0,
        dest='interval',
        help="number of seconds between each ping (defaults to 1)",
        type=float,
    )
    parser.add_argument(
        "-l",
        "--loss-tolerance",
        default=1,
        dest='loss_tolerance',
        help="number of consecutive timeouts until TARGET is considered down (defaults to 1)",
        type=int,
    )
    parser.add_argument(
        "-q",
        "--quit-up",
        action='store_true',
        dest='quit_up',
        help="quit when TARGET is up",
    )
    parser.add_argument(
        "-Q",
        "--quit-down",
        action='store_true',
        dest='quit_down',
        help="quit when TARGET is down",
    )
    parser.add_argument(
        "-s",
        "--size",
        default=56,
        dest='payload_size',
        help="payload size in bytes (defaults to 56)",
        type=int,
    )
    parser.add_argument(
        "-t",
        "--timeout",
        default=2.0,
        dest='timeout',
        help="number of seconds before a ping is considered lost (defaults to 2)",
        type=float,
    )
    parser.add_argument(
        "--version",
        action='version',
        version=VERSION_STRING,
    )
    return parser


def main(*args, **kwargs):
    if not args:
        args = argv[1:]

    parser = build_parser()
    pargs = parser.parse_args(args)

    ping_recorder = PingRecorder(
        pargs.target,
        count=pargs.count,
        interval=pargs.interval,
        payload_size=pargs.payload_size,
        timeout=pargs.timeout,
    )
    ping_recorder.start()
    try:
        run_ui(ping_recorder, pargs)
    except KeyboardInterrupt:
        pass
    finally:
        ping_recorder.stop()
    print(ping_recorder.report_stats())
