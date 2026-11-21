"""Shared figure styling so every plot on the site reads as one family."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

PAGE_BG = "#f4f1e8"
TEAL = "#26736d"
ORANGE = "#d17b39"
SLATE = "#48565a"
PLUM = "#7d5a76"
SAND = "#b9a37e"
INK = "#202a2e"

SEQUENCE = [TEAL, ORANGE, PLUM, SAND, SLATE]
FORMAT_COLOURS = {"ODI": TEAL, "T20": ORANGE}
RESULT_COLOURS = {"Defended": TEAL, "Chased": ORANGE}

OUTPUT_DIR = Path(__file__).resolve().parent

plt.rcParams.update({
    "figure.facecolor": PAGE_BG,
    "axes.facecolor": PAGE_BG,
    "savefig.facecolor": PAGE_BG,
    "font.family": "DejaVu Sans",
    "font.size": 11,
    "axes.titlesize": 14,
    "axes.titleweight": "bold",
    "axes.labelsize": 11.5,
    "axes.labelcolor": INK,
    "axes.edgecolor": SLATE,
    "text.color": INK,
    "xtick.color": SLATE,
    "ytick.color": SLATE,
    "legend.frameon": False,
    "figure.autolayout": False,
})


def new_axes(width: float = 9.0, height: float = 5.0):
    """Return a figure and axis with the project's default frame."""
    figure, axis = plt.subplots(figsize=(width, height))
    axis.grid(alpha=0.16, linewidth=0.8)
    axis.set_axisbelow(True)
    axis.spines[["top", "right"]].set_visible(False)
    return figure, axis


def finish(figure, axis, filename: str, title: str, xlabel: str = "", ylabel: str = "") -> None:
    """Apply the title and labels, then write the figure to the analysis folder."""
    axis.set_title(title, loc="left", pad=12)
    if xlabel:
        axis.set_xlabel(xlabel)
    if ylabel:
        axis.set_ylabel(ylabel)
    figure.tight_layout()
    figure.savefig(OUTPUT_DIR / filename, dpi=150, bbox_inches="tight")
    plt.close(figure)
    print(f"    wrote {filename}", flush=True)


def save(figure, filename: str) -> None:
    """Write a figure that has already been fully composed."""
    figure.tight_layout()
    figure.savefig(OUTPUT_DIR / filename, dpi=150, bbox_inches="tight")
    plt.close(figure)
    print(f"    wrote {filename}", flush=True)


def shorten(text: str, limit: int = 28) -> str:
    """Trim a long venue or team name so axis ticks stay readable."""
    text = str(text)
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"


def _draw_table(axis, display, fontsize: float) -> None:
    axis.axis("off")
    table = axis.table(
        cellText=display.values,
        colLabels=[shorten(c, 22) for c in display.columns],
        loc="center",
        cellLoc="center",
    )
    table.auto_set_font_size(False)
    table.set_fontsize(fontsize)
    table.scale(1, 1.5)

    for (row, _), cell in table.get_celld().items():
        cell.set_edgecolor("#d8d2c2")
        cell.set_linewidth(0.8)
        if row == 0:
            cell.set_facecolor(TEAL)
            cell.set_text_props(color="white", fontweight="bold")
        else:
            cell.set_facecolor("#fbfaf6" if row % 2 else "#f0ece0")


def table_figure(frame, filename: str, title: str, subtitle: str = "",
                 max_columns: int = 8, width: float = 13.0,
                 wrap_columns: int | None = None, fontsize: float = 8.5) -> None:
    """Render a small slice of a dataframe as a readable table image.

    Only the first ``max_columns`` columns are drawn; a wide frame is reported
    in the subtitle instead of being squeezed into unreadable text.

    With ``wrap_columns`` every column is drawn, split into stacked blocks of
    that many columns. The first column (a label or an ID) is repeated at the
    start of each block so every row can still be read across.
    """
    if wrap_columns is None:
        blocks = [frame.iloc[:, :max_columns]]
    else:
        key, rest = frame.columns[0], list(frame.columns[1:])
        step = max(1, wrap_columns - 1)
        blocks = [frame[[key] + rest[i:i + step]] for i in range(0, len(rest), step)]

    shown = []
    for block in blocks:
        display = block.copy()
        for column in display.columns:
            display[column] = display[column].map(lambda v: shorten(v, 20))
        shown.append(display)

    block_height = 0.38 + 0.30 * len(frame)
    figure, axes = plt.subplots(len(shown), 1,
                                figsize=(width, 0.55 + block_height * len(shown)),
                                squeeze=False)
    for axis, display in zip(axes[:, 0], shown):
        _draw_table(axis, display, fontsize)

    heading = title if not subtitle else f"{title}\n{subtitle}"
    axes[0, 0].set_title(heading, loc="left", pad=14, fontsize=13)
    save(figure, filename)
