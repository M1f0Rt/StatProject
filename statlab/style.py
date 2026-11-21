"""Единая палитра и оформление графиков"""
import numpy as np
import seaborn as sns
from matplotlib import patheffects

METHOD_COLORS = {
    "r2SCAN": "#2a78d6",
    "NN-r2SCAN": "#eb6834",
    "delta": "#1baf7a",
}

TYPES = ["BH", "TC", "ISO", "INC", "NC"]
TYPE_COLORS = {
    "BH": "#e34948",
    "TC": "#6250d6",
    "ISO": "#008300",
    "INC": "#e87ba4",
    "NC": "#eda100",
}

THEME = {
    "background": "#FFFFFF",
    "text": "#172B43",
    "grid": "#DEE6EF",
    "axis": "#B6C2CF",
    "font": "Arial",
    "font_size": 14,
    "height": 410,
}

ROLE_COLORS = {
    "model": THEME["text"],
    "reference": THEME["text"],
    "generator": "#898781",
}

# Последовательная шкала (величина от малой к большой): один синий тон, от светлого к тёмному
SEQUENTIAL = ["#cde2fb", "#86b6ef", "#3987e5", "#1c5cab", "#0d366b"]

# Стандартные размеры фигур matplotlib, дюймы: на всю ширину (одна, две или три панели) и квадрат
FIGSIZE = {
    "full": (12, 4),
    "square": (6, 6),
}


def blend(color, other, share):
    """Смесь двух цветов: share - доля второго цвета."""
    a, b = (np.array([int(c[i:i + 2], 16) for i in (1, 3, 5)]) for c in (color, other))
    return "#" + "".join(f"{round(v):02x}" for v in a + (b - a) * share)


def css_vars():
    """CSS-переменные оформления marimo-страницы, чтобы её цвета тоже брались из этого модуля."""
    return ";".join([
        f"--lab-ink:{THEME['text']}",
        f"--lab-ink-soft:{blend(THEME['text'], THEME['background'], 0.3)}",
        f"--lab-grid:{THEME['grid']}",
        f"--lab-surface:{blend(THEME['grid'], THEME['background'], 0.6)}",
        f"--lab-font:{THEME['font']}, sans-serif",
    ])


def setup_matplotlib():
    """Тема seaborn/matplotlib. Палитра по умолчанию - цвета типов в порядке TYPES."""
    sns.set_theme(style="whitegrid", palette=[TYPE_COLORS[t] for t in TYPES], rc={
        "figure.facecolor": THEME["background"], "axes.facecolor": THEME["background"],
        "figure.figsize": FIGSIZE["full"],
        "text.color": THEME["text"], "axes.labelcolor": THEME["text"],
        "xtick.color": THEME["text"], "ytick.color": THEME["text"],
        "axes.edgecolor": THEME["axis"], "axes.linewidth": 0.8,
        "axes.spines.top": False, "axes.spines.right": False,
        "grid.color": THEME["grid"], "grid.linewidth": 0.6,
        "legend.frameon": False, "axes.titleweight": "bold",
        "font.family": "sans-serif", "font.sans-serif": [THEME["font"], "DejaVu Sans"],
        "font.size": THEME["font_size"] * 0.75,
    })
    from IPython import get_ipython

    shell = get_ipython()
    if shell is not None:
        shell.run_line_magic("config", "InlineBackend.figure_format = 'retina'")


def label_curves(ax, x, curves, pad=6, x_range=None):
    """Подписи кривых прямо на графике, в дополнение к легенде.

    Каждая подпись ставится там, где её кривая дальше всего отстоит от остальных
    (в пределах x_range, если он задан), поэтому вызывать функцию нужно после того,
    как заданы пределы осей.
    """
    x = np.asarray(x, float)
    fontsize = THEME["font_size"] * 0.7
    lo, hi = ax.get_xlim()
    inside = (x > lo + 0.05 * (hi - lo)) & (x < hi - 0.05 * (hi - lo))
    if x_range is not None:
        inside &= (x >= x_range[0]) & (x <= x_range[1])
    box = ax.get_window_extent()
    room = (pad + fontsize) * ax.figure.dpi / 72
    with np.errstate(divide="ignore", invalid="ignore"):
        px = {name: ax.transData.transform(np.column_stack([x, y]))[:, 1] for name, y in curves.items()}
    for name, y in curves.items():
        others = np.array([p for other, p in px.items() if other != name])
        ok = inside & np.isfinite(px[name]) & np.isfinite(others).all(axis=0)
        above = np.where(ok & (px[name] + room < box.y1), px[name] - others.max(axis=0), -np.inf)
        below = np.where(ok & (px[name] - room > box.y0), others.min(axis=0) - px[name], -np.inf)
        on_top = above.max() > room / 2 or above.max() >= below.max()
        i = int(np.argmax(above if on_top else below))
        ax.annotate(name, (x[i], np.asarray(y)[i]), xytext=(0, pad if on_top else -pad),
                    textcoords="offset points", ha="center", va="bottom" if on_top else "top",
                    fontsize=fontsize, color=THEME["text"],
                    path_effects=[patheffects.withStroke(linewidth=3, foreground=THEME["background"])])


def style_chart(fig, title, x_label, y_label, legend_title=""):
    """Оформление plotly-графика. title=None - без заголовка (в marimo его заменяет раздел)."""
    fig.update_layout(
        template="plotly_white", title=title, height=THEME["height"],
        paper_bgcolor=THEME["background"], plot_bgcolor=THEME["background"],
        font=dict(family=THEME["font"], size=THEME["font_size"], color=THEME["text"]),
        margin=dict(l=72, r=28, t=84 if title else 64, b=60),
        legend=dict(title_text=legend_title, orientation="h", x=0, y=1.02, yanchor="bottom"),
        hoverlabel=dict(namelength=-1),
    )
    fig.update_xaxes(title_text=x_label, gridcolor=THEME["grid"], automargin=True)
    fig.update_yaxes(title_text=y_label, gridcolor=THEME["grid"], automargin=True)
    return fig
