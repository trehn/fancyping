import curses
from datetime import datetime
from time import sleep

COLOR_FULL_BLACK = 1
COLOR_FULL_RED = 2
COLOR_FULL_BLUE = 3
COLOR_FULL_GREEN = 4
COLOR_DEFAULT = 5
COLOR_RED = 6
COLOR_GREEN = 7

STATS_INTERVALS = [
    (10, "10s"),
    (30, "30s"),
    (60, "60s"),
    (60 * 2, "2m"),
    (60 * 5, "5m"),
    (60 * 10, "10m"),
    (60 * 15, "15m"),
    (60 * 30, "30m"),
    (60 * 60, "1h"),
    (60 * 60 * 3, "3h"),
    (60 * 60 * 6, "6h"),
    (60 * 60 * 12, "12h"),
    (60 * 60 * 24, "24h"),
]


def init_colors():
    curses.use_default_colors()
    curses.init_pair(COLOR_FULL_BLACK, curses.COLOR_BLACK, curses.COLOR_BLACK)
    curses.init_pair(COLOR_FULL_RED, curses.COLOR_RED, curses.COLOR_RED)
    curses.init_pair(COLOR_FULL_BLUE, curses.COLOR_BLUE, curses.COLOR_BLUE)
    curses.init_pair(COLOR_FULL_GREEN, curses.COLOR_GREEN, curses.COLOR_GREEN)
    curses.init_pair(COLOR_DEFAULT, -1, -1)
    curses.init_pair(COLOR_RED, curses.COLOR_RED, -1)
    curses.init_pair(COLOR_GREEN, curses.COLOR_GREEN, -1)
    try:
        curses.curs_set(False)
    except curses.error:
        # fails on some terminals
        pass


def time_since(prior_time):
    tsec = (datetime.utcnow() - prior_time).total_seconds()
    h, remainder = divmod(tsec, 3600)
    m, s = divmod(remainder, 60)
    result = f"{int(s)}s ago"
    if m:
        result = f"{int(m)}m {result}"
    if h:
        result = f"{int(h)}h {result}"
    return result


def draw_text(win, y, x, lines, max_line_length, alive):
    text_color = COLOR_GREEN if alive else COLOR_RED
    for i, line in enumerate(lines):
        win.addstr(y + 2 + i, x + 4, line.center(max_line_length), curses.color_pair(text_color))


def draw_center_box(win, lines, max_line_length, alive):
    box_height = len(lines) + 4
    box_width = max_line_length + 8
    y = int((curses.LINES - box_height) / 2) - 1
    x = int((curses.COLS - box_width) / 2) - 1
    for tick_values in ticks(y, x, box_height, box_width):
        win.addstr(*tick_values, curses.color_pair(COLOR_FULL_BLACK))
    return y, x, box_height, box_width


def tick_center_box(win, y, x, box_height, box_width, alive, anim):
    color = COLOR_FULL_GREEN if alive else COLOR_FULL_RED
    number_of_ticks = box_width * 2 + (box_height - 2) * 2
    tick_values = list(ticks(y, x, box_height, box_width))
    while True:
        for draw_index in range(number_of_ticks):
            delete_index = (draw_index + int(number_of_ticks / 2)) % number_of_ticks
            win.addstr(
                *tick_values[draw_index],
                curses.color_pair(color),
            )
            win.addstr(
                *tick_values[delete_index],
                curses.color_pair(COLOR_FULL_BLACK if anim else color),
            )
            yield number_of_ticks


def ticks(y, x, box_height, box_width):
    for i in range(0, box_width):
        yield y, x + i, " "
    for i in range(0, box_height - 2):
        yield y + 1 + i, x + box_width - 2, "  "
    for i in range(0, box_width):
        yield y + box_height - 1, x + box_width - 1 - i, " "
    for i in range(0, box_height - 2):
        yield y + box_height - 2 - i, x, "  "


def run_ui(ping_recorder, options):
    curses.wrapper(main, ping_recorder, options)


def main(stdscr, ping_recorder, options):
    stdscr.clear()
    stdscr.nodelay(True)
    init_colors()

    previous_state = None
    stats_interval_index = 2

    while True:
        try:
            key = stdscr.getkey()
        except curses.error:
            pass
        else:
            if key in ("q", "Q"):
                break
            elif key in ("r", "R"):
                ping_recorder.reset()
                previous_state = None
            elif key == "+" and stats_interval_index < len(STATS_INTERVALS) - 1:
                stats_interval_index += 1
                previous_state = None
            elif key == "-" and stats_interval_index > 0:
                stats_interval_index -= 1
                previous_state = None

        if ping_recorder.updated.is_set() or previous_state is None:
            ping_recorder.updated.clear()
            last_rtt = ping_recorder.last_rtt
            if last_rtt:
                rtt_text = f"RTT {last_rtt:9.2f}ms"
                alive = True
            else:
                rtt_text = ping_recorder.error or ""
                alive = False
            stats_interval, stats_interval_desc = STATS_INTERVALS[stats_interval_index]
            lines = [
                ping_recorder.target,
                "",
                rtt_text,
                "",
                f"- {stats_interval_desc} +",
            ]
            rtt_stats = ping_recorder.rtt_stats(stats_interval)
            if rtt_stats:
                lines.extend([
                    f"AVG {rtt_stats[0]:9.2f}ms",
                    f"MED {rtt_stats[1]:9.2f}ms",
                    f"MIN {rtt_stats[2]:9.2f}ms",
                    f"MAX {rtt_stats[3]:9.2f}ms",
                ])
            lines.append(f"P/L {ping_recorder.packet_loss(stats_interval) * 100:10.1f}%")

            if alive and ping_recorder.last_down:
                lines.extend([
                    "",
                    "LAST P/L",
                    time_since(ping_recorder.last_down),
                ])
            elif not alive and ping_recorder.last_alive:
                lines.extend([
                    "",
                    "LAST UP",
                    time_since(ping_recorder.last_alive),
                ])

            max_line_length = max([len(line) for line in lines])
            redraw_text = True
        else:
            redraw_text = False

        state = (
            alive,
            len(lines),
            max_line_length,
            stdscr.getmaxyx(),
        )

        if state != previous_state:
            previous_state = state
            stdscr.clear()
            box_height = len(lines) + 4
            box_width = max_line_length + 8
            max_y, max_x = stdscr.getmaxyx()
            y = int((max_y - box_height) / 2) - 1
            x = int((max_x - box_width) / 2) - 1
            anim = (alive and options.anim_up) or (not alive and options.anim_down)
            ticker = tick_center_box(stdscr, y, x, box_height, box_width, alive, anim)

        if redraw_text:
            draw_text(stdscr, y, x, lines, max_line_length, alive)

        number_of_ticks = next(ticker)
        stdscr.refresh()
        sleep(1 / number_of_ticks)
