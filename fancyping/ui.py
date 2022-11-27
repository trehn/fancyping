from copy import deepcopy
import curses
from datetime import datetime
from time import sleep
from types import SimpleNamespace

COLOR_FULL_BLACK = 1
COLOR_FULL_RED = 2
COLOR_FULL_BLUE = 3
COLOR_FULL_GREEN = 4
COLOR_DEFAULT = 5
COLOR_RED = 6
COLOR_GREEN = 7

HISTOGRAM_CHARS = [
    "▁",
    "▂",
    "▃",
    "▄",
    "▅",
    "▆",
    "▇",
    "█",
]

INITIAL_STATE = SimpleNamespace(
    alive=None,
    box_height=0,
    box_origin_x=0,
    box_origin_y=0,
    box_width=0,
    histogram_columns=[],
    histogram_y=[],
    lines=[],
    max_line_length=0,
    screen_size=(0, 0),
    stats_interval_index=2,
)


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


def draw_text(win, state):
    text_color = COLOR_GREEN if state.alive else COLOR_RED
    for i, line in enumerate(state.lines):
        win.addstr(
            state.box_origin_y + 2 + i, state.box_origin_x + 4,
            line.center(state.max_line_length),
            curses.color_pair(text_color),
        )


def draw_full_color(win, state):
    if state.alive is None:
        return
    color = COLOR_FULL_GREEN if state.alive else COLOR_FULL_RED
    y, x = state.box_origin_y, state.box_origin_x
    full_height, full_width = win.getmaxyx()
    for i in range(full_height - 1):
        for j in range(full_width - 1):
            if state.histogram_y and i == min(state.histogram_y) - 1:
                continue
            if not (
                i >= y - 1 and i <= y + state.box_height and
                j >= x - 2 and j <= x + state.box_width + 1
            ) and i not in state.histogram_y:
                win.addstr(i, j, " ", curses.color_pair(color))


def tick_box(win, state, anim):
    color = COLOR_FULL_GREEN if state.alive else COLOR_FULL_RED
    number_of_ticks = state.box_width * 2 + (state.box_height - 2) * 2
    tick_values = list(ticks(
        state.box_origin_y,
        state.box_origin_x,
        state.box_height,
        state.box_width,
    ))
    while True:
        for draw_index in range(number_of_ticks):
            delete_index = (draw_index + int(number_of_ticks / 2)) % number_of_ticks
            if state.alive is not None:
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


def box_text(ping_recorder, state):
    if state.alive:
        last_rtt = ping_recorder.last_rtt
        if last_rtt is None:
            rtt_text = ping_recorder.error or ""
        else:
            rtt_text = f"RTT {last_rtt:9.2f}ms"
    else:
        rtt_text = ping_recorder.error or ""
    stats_interval, stats_interval_desc = \
        ping_recorder.STATS_INTERVALS[state.stats_interval_index]
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

    if state.alive and ping_recorder.last_pl:
        lines.extend([
            "",
            "LAST P/L",
            time_since(ping_recorder.last_pl),
        ])
    elif not state.alive and ping_recorder.last_resp:
        lines.extend([
            "",
            "LAST UP",
            time_since(ping_recorder.last_resp),
        ])
    return lines


def draw_histogram(win, state):
    for i, column in enumerate(state.histogram_columns):
        if i >= state.screen_size[1] - 2:
            return
        if column is None:
            for y in state.histogram_y:
                win.addstr(
                    y, state.screen_size[1] - 2 - i,
                    " ",
                    curses.color_pair(COLOR_FULL_RED),
                )
        else:
            for y, char in zip(state.histogram_y, column[1:]):
                win.addstr(
                    y, state.screen_size[1] - 2 - i,
                    char,
                    curses.color_pair(COLOR_GREEN),
                )


def histogram_column(rtt, number_of_lines, upper):
    if rtt is None:
        return None
    value = min(rtt, upper) / upper
    line_value = 1 / number_of_lines
    result = [rtt]
    for i in range(number_of_lines):
        if value is None:
            result.append(" ")
        elif value > line_value:
            result.append(HISTOGRAM_CHARS[-1])
            value -= line_value
        else:
            result.append(HISTOGRAM_CHARS[
                int(round((value / line_value) * (len(HISTOGRAM_CHARS) - 1)))
            ])
            value = None
    return result


def main(stdscr, ping_recorder, options):
    stdscr.clear()
    stdscr.nodelay(True)
    init_colors()

    previous_state = deepcopy(INITIAL_STATE)
    ticker = None

    while not ping_recorder.stopped.is_set():
        state = deepcopy(previous_state)
        state.screen_size = stdscr.getmaxyx()
        try:
            key = stdscr.getkey()
        except curses.error:
            pass
        else:
            if key in ("q", "Q"):
                break
            elif key in ("r", "R"):
                ping_recorder.report_write_full()
            elif key in ("x", "X"):
                ping_recorder.reset()
                previous_state = deepcopy(INITIAL_STATE)
                continue
            elif key == "+" and state.stats_interval_index < len(ping_recorder.STATS_INTERVALS) - 1:
                state.stats_interval_index += 1
            elif key == "-" and state.stats_interval_index > 0:
                state.stats_interval_index -= 1

        if ping_recorder.updated.is_set():
            ping_recorder.updated.clear()
            state.alive = ping_recorder.is_alive(options.loss_tolerance)
            state.lines = box_text(ping_recorder, state)
            state.max_line_length = max([len(line) for line in state.lines])
            if options.histogram_lines > 0 and state.alive is not None:
                state.histogram_columns.insert(
                    0,
                    histogram_column(
                        ping_recorder.last_rtt,
                        options.histogram_lines,
                        options.histogram_upper,
                    ),
                )
                if len(state.histogram_columns) > state.screen_size[1]:
                    state.histogram_columns.pop()

        if state.alive != previous_state.alive:
            if previous_state.alive is not None:
                curses.beep()
            if state.alive is True and options.quit_up:
                break
            elif state.alive is False and options.quit_down:
                break

        if (
            len(state.lines) != len(previous_state.lines) or
            state.max_line_length != previous_state.max_line_length or
            state.alive != previous_state.alive or
            state.screen_size != previous_state.screen_size
        ):
            stdscr.clear()
            state.box_height = len(state.lines) + 4
            state.box_width = state.max_line_length + 8
            max_y, max_x = state.screen_size
            histogram_lines = min(options.histogram_lines, max_y - state.box_height - 1)
            state.box_origin_y = int((max_y - histogram_lines - state.box_height) / 2)
            state.box_origin_x = int((max_x - state.box_width) / 2)
            state.histogram_y = list(range(max_y - 1, max_y - 1 - histogram_lines, -1))

            anim = (state.alive and options.anim_up) or (not state.alive and options.anim_down)
            ticker = None if state.alive is None else tick_box(stdscr, state, anim)

            if (
                (state.alive is True and options.color_up) or
                (state.alive is False and options.color_down)
            ):
                draw_full_color(stdscr, state)

        if state.lines != previous_state.lines:
            draw_text(stdscr, state)

        if state.histogram_columns != previous_state.histogram_columns:
            draw_histogram(stdscr, state)

        if ticker:
            sleep_amount = options.interval / next(ticker)
        else:
            sleep_amount = 0.1
        stdscr.refresh()
        previous_state = deepcopy(state)
        sleep(max(sleep_amount, 1 / 60))
