import json
import sys
import textwrap

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


BG = "#fbfbf8"
TEXT = "#24292f"
MUTED = "#6e7781"
GRID = "#d8dee4"
BLUE = "#4f6f91"
GREEN = "#2f7f73"
GOLD = "#c58b2a"
RED = "#b05c4b"
PURPLE = "#7467a8"
TEAL = "#3f8f9f"
PALETTE = [BLUE, GREEN, GOLD, RED, PURPLE, TEAL]


def short_number(value):
    value = int(value)
    sign = "-" if value < 0 else ""
    value = abs(value)
    if value >= 1_000_000:
        return f"{sign}{value / 1_000_000:.2f}M"
    if value >= 1_000:
        return f"{sign}{value / 1_000:.1f}K"
    return f"{sign}{value:,}"


def wrapped(label, width=28):
    return textwrap.fill(label, width=width, break_long_words=False)


def flatten_counts(data, mode):
    rows = []
    language_totals_only = str(mode).startswith("1")

    for language, (total, dialects) in data.items():
        if language_totals_only:
            rows.append((language, int(total)))
            continue

        for dialect, count in dialects.items():
            label = language if dialect == "Not Specified" else f"{language}: {dialect}"
            rows.append((label, int(count)))

    return [(label, count) for label, count in rows if count]


def draw_empty(title, output_path):
    fig, ax = plt.subplots(figsize=(10, 4), facecolor=BG)
    ax.set_facecolor(BG)
    ax.axis("off")
    ax.text(0.02, 0.70, title, color=TEXT, fontsize=18, fontweight="bold", transform=ax.transAxes)
    ax.text(0.02, 0.48, "No non-zero token counts to plot.", color=MUTED, fontsize=11, transform=ax.transAxes)
    fig.savefig(output_path, dpi=180, bbox_inches="tight", facecolor=BG)
    plt.close(fig)


def draw_bar_chart(rows, title, output_path, max_rows):
    if not rows:
        draw_empty(title, output_path)
        return

    total_rows = len(rows)
    rows = sorted(rows, key=lambda item: item[1], reverse=True)[:max_rows]
    rows = list(reversed(rows))

    labels = [wrapped(label) for label, _count in rows]
    values = [count for _label, count in rows]
    colors = [PALETTE[i % len(PALETTE)] for i in range(len(rows))]

    height = max(5.0, min(16.0, 0.38 * len(rows) + 2.4))
    fig, ax = plt.subplots(figsize=(11, height), facecolor=BG)
    ax.set_facecolor(BG)

    bars = ax.barh(labels, values, color=colors, height=0.68)
    ax.set_title(title, loc="left", fontsize=18, fontweight="bold", color=TEXT, pad=16)
    note = f"Showing top {len(rows)} of {total_rows} rows by token count."
    ax.text(0, 1.01, note, transform=ax.transAxes, ha="left", va="bottom", fontsize=10, color=MUTED)

    ax.set_xlabel("Tokens", color=MUTED, labelpad=10)
    ax.xaxis.set_major_formatter(lambda value, _pos: short_number(value))
    ax.grid(axis="x", color=GRID, linewidth=0.8, alpha=0.8)
    ax.set_axisbelow(True)
    ax.tick_params(axis="x", colors=MUTED, labelsize=9)
    ax.tick_params(axis="y", colors=TEXT, labelsize=9, length=0)

    for spine in ["top", "right", "left"]:
        ax.spines[spine].set_visible(False)
    ax.spines["bottom"].set_color(GRID)

    xmax = max(values) * 1.16 if values else 1
    ax.set_xlim(0, xmax)
    for bar, value in zip(bars, values):
        ax.text(
            bar.get_width() + xmax * 0.01,
            bar.get_y() + bar.get_height() / 2,
            short_number(value),
            va="center",
            ha="left",
            fontsize=9,
            color=MUTED,
        )

    fig.tight_layout()
    fig.savefig(output_path, dpi=180, bbox_inches="tight", facecolor=BG)
    plt.close(fig)


def plot_charts(path, mode):
    with open(path) as f:
        data = json.load(f)

    language_totals_only = str(mode).startswith("1")
    title = "Language Token Counts" if language_totals_only else "Language and Dialect Token Counts"
    max_rows = 25 if language_totals_only else 40
    rows = flatten_counts(data, mode)
    draw_bar_chart(rows, title, "plot.png", max_rows=max_rows)


if __name__ == "__main__":
    path = sys.argv[1]
    mode = sys.argv[2]
    plot_charts(path, mode)
