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
POSITIVE = "#2f7f73"
NEGATIVE = "#b05c4b"


def short_number(value):
    value = int(value)
    sign = "-" if value < 0 else ""
    value = abs(value)
    if value >= 1_000_000:
        return f"{sign}{value / 1_000_000:.2f}M"
    if value >= 1_000:
        return f"{sign}{value / 1_000:.1f}K"
    return f"{sign}{value:,}"


def signed_number(value):
    return f"{'+' if value > 0 else ''}{short_number(value)}"


def wrapped(label, width=30):
    return textwrap.fill(label, width=width, break_long_words=False)


def flatten_deltas(data):
    rows = []
    for language, (total, dialects) in data.items():
        if total:
            rows.append((f"{language} total", int(total)))
        for dialect, delta in dialects.items():
            if delta:
                label = language if dialect == "Not Specified" else f"{language}: {dialect}"
                rows.append((label, int(delta)))
    return rows


def draw_empty(output_path):
    fig, ax = plt.subplots(figsize=(10, 4), facecolor=BG)
    ax.set_facecolor(BG)
    ax.axis("off")
    ax.text(0.02, 0.70, "Token Count Delta", color=TEXT, fontsize=18, fontweight="bold", transform=ax.transAxes)
    ax.text(0.02, 0.48, "No token count changes detected.", color=MUTED, fontsize=11, transform=ax.transAxes)
    fig.savefig(output_path, dpi=180, bbox_inches="tight", facecolor=BG)
    plt.close(fig)


def plot_charts(deltas_path):
    with open(deltas_path) as f:
        data = json.load(f)

    rows = flatten_deltas(data)
    if not rows:
        draw_empty("language_dialect_deltas.png")
        return

    total_rows = len(rows)
    rows = sorted(rows, key=lambda item: abs(item[1]), reverse=True)[:40]
    rows = sorted(rows, key=lambda item: item[1])

    labels = [wrapped(label) for label, _delta in rows]
    values = [delta for _label, delta in rows]
    colors = [POSITIVE if value > 0 else NEGATIVE for value in values]
    limit = max(abs(value) for value in values) * 1.18

    height = max(5.0, min(16.0, 0.40 * len(rows) + 2.4))
    fig, ax = plt.subplots(figsize=(11, height), facecolor=BG)
    ax.set_facecolor(BG)

    bars = ax.barh(labels, values, color=colors, height=0.68)
    ax.axvline(0, color="#8c959f", linewidth=1)
    ax.set_xlim(-limit, limit)
    ax.set_title("Token Count Delta", loc="left", fontsize=18, fontweight="bold", color=TEXT, pad=16)
    ax.text(
        0,
        1.01,
        f"Showing top {len(rows)} of {total_rows} non-zero rows by absolute change.",
        transform=ax.transAxes,
        ha="left",
        va="bottom",
        fontsize=10,
        color=MUTED,
    )

    ax.set_xlabel("Token change", color=MUTED, labelpad=10)
    ax.xaxis.set_major_formatter(lambda value, _pos: short_number(value))
    ax.grid(axis="x", color=GRID, linewidth=0.8, alpha=0.8)
    ax.set_axisbelow(True)
    ax.tick_params(axis="x", colors=MUTED, labelsize=9)
    ax.tick_params(axis="y", colors=TEXT, labelsize=9, length=0)

    for spine in ["top", "right", "left"]:
        ax.spines[spine].set_visible(False)
    ax.spines["bottom"].set_color(GRID)

    for bar, value in zip(bars, values):
        x = bar.get_width()
        label_x = x + (limit * 0.025 if value > 0 else -limit * 0.025)
        ax.text(
            label_x,
            bar.get_y() + bar.get_height() / 2,
            signed_number(value),
            va="center",
            ha="left" if value > 0 else "right",
            fontsize=9,
            color=MUTED,
        )

    fig.tight_layout()
    fig.savefig("language_dialect_deltas.png", dpi=180, bbox_inches="tight", facecolor=BG)
    plt.close(fig)


if __name__ == "__main__":
    deltas_path = sys.argv[1]
    plot_charts(deltas_path)
