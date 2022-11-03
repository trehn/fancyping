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
  R   reset stats
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
        "-i",
        "--interval",
        default=1.0,
        dest='interval',
        help="number of seconds between each ping (defaults to 1)",
        type=float,
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
        "-D",
        "--no-down-anim",
        action='store_false',
        dest='anim_down',
        help="disable animation while TARGET is down",
    )
    parser.add_argument(
        "-U",
        "--no-up-anim",
        action='store_false',
        dest='anim_up',
        help="disable animation while TARGET is up",
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
        interval=pargs.interval,
        timeout=pargs.timeout,
    )
    ping_recorder.start()
    try:
        run_ui(ping_recorder, pargs)
    except KeyboardInterrupt:
        pass
    finally:
        ping_recorder.stop()
