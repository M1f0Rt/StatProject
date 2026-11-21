import argparse
import base64
import io
import json
import subprocess
import sys
import warnings
from itertools import combinations
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import nbformat
import numpy as np
from matplotlib import font_manager
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
ASSETS, EXPORT = HERE / "assets", HERE / "export"
sys.path.insert(0, str(ROOT))
from statlab.style import METHOD_COLORS, ROLE_COLORS, THEME, TYPE_COLORS, TYPES, setup_matplotlib  # noqa: E402

BEFORE_COMMIT = "e1a03bc1"  # последняя версия ноутбука инфохимиков до оформления

# --- цвет: OKLab и модель дальтонизма Machado, Oliveira, Fernandes (2009), полная степень ---
MACHADO = {
    "протанопия": np.array([[0.152286, 1.052583, -0.204868],
                            [0.114503, 0.786281, 0.099216],
                            [-0.003882, -0.048116, 1.051998]]),
    "дейтеранопия": np.array([[0.367322, 0.860646, -0.227968],
                              [0.280085, 0.672501, 0.047413],
                              [-0.011820, 0.042940, 0.968881]]),
}
LMS = np.array([[0.4122214708, 0.5363325363, 0.0514459929],
                [0.2119034982, 0.6806995451, 0.1073969566],
                [0.0883024619, 0.2817188376, 0.6299787005]])
LAB = np.array([[0.2104542553, 0.7936177850, -0.0040720468],
                [1.9779984951, -2.4285922050, 0.4505937099],
                [0.0259040371, 0.7827717662, -0.8086757660]])


def to_linear(color):
    c = np.array([int(color[i:i + 2], 16) / 255 for i in (1, 3, 5)])
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def to_hex(linear):
    c = np.clip(linear, 0, 1)
    s = np.where(c <= 0.0031308, 12.92 * c, 1.055 * c ** (1 / 2.4) - 0.055)
    return "#" + "".join(f"{round(v * 255):02x}" for v in s)


def simulate(color, vision=None):
    lin = to_linear(color)
    return lin if vision is None else np.clip(MACHADO[vision] @ lin, 0, 1)


def delta_e(a, b, vision=None):
    lab = lambda c: LAB @ np.cbrt(LMS @ simulate(c, vision))
    return 100 * np.linalg.norm(lab(a) - lab(b))


def contrast(a, b):
    lum = lambda c: to_linear(c) @ [0.2126, 0.7152, 0.0722]
    hi, lo = sorted([lum(a), lum(b)], reverse=True)
    return (hi + 0.05) / (lo + 0.05)


# --- карточка палитры ------------------------------------------------------------
VISIONS = [("Обычное зрение", None), ("Протанопия", "протанопия"), ("Дейтеранопия", "дейтеранопия")]
GROUPS = [
    ("Величины", [("r2SCAN", METHOD_COLORS["r2SCAN"]), ("NN-r2SCAN", METHOD_COLORS["NN-r2SCAN"]),
                  ("Δ", METHOD_COLORS["delta"])], "all"),
    ("Типы реакций", [(t, TYPE_COLORS[t]) for t in TYPES], "adjacent"),
    ("Нейтральные роли", [("модель", ROLE_COLORS["model"]), ("опорная\nлиния", ROLE_COLORS["reference"]),
                          ("генератор", ROLE_COLORS["generator"])], None),
]


def worst_delta_e(colors, pairs, vision):
    pairlist = combinations(colors, 2) if pairs == "all" else zip(colors, colors[1:])
    return min(delta_e(a, b, vision) for a, b in pairlist)


def build_palette():
    setup_matplotlib()
    fig, axes = plt.subplots(len(GROUPS), len(VISIONS), figsize=(16, 7.6))
    for row, (group, swatches, pairs) in enumerate(GROUPS):
        colors = [c for _, c in swatches]
        for col, (title, vision) in enumerate(VISIONS):
            ax = axes[row, col]
            ax.set(xlim=(0, 5), ylim=(-0.62, 1))
            ax.axis("off")
            if row == 0:
                ax.set_title(title, fontsize=14, pad=12)
            if col == 0:
                ax.text(-0.15, 0.5, group, ha="right", va="center", fontsize=13, weight="bold",
                        color=THEME["text"], clip_on=False)
            for i, (name, color) in enumerate(swatches):
                shown = to_hex(simulate(color, vision))
                ax.add_patch(plt.Rectangle((i, 0.3), 0.92, 0.7, color=shown))
                ax.text(i + 0.46, 0.15, name, ha="center", va="center", color=THEME["text"], fontsize=11,
                        weight="bold", linespacing=0.95)
                if vision is None:
                    ink = "#ffffff" if contrast(color, "#ffffff") >= contrast(color, THEME["text"]) else THEME["text"]
                    ax.text(i + 0.46, 0.65, color.lower(), ha="center", va="center", color=ink, fontsize=10)
            if pairs:
                d = worst_delta_e(colors, pairs, vision)
                limit = 15 if vision is None else 8
                where = "все пары" if pairs == "all" else "соседние пары"
                note = f"мин. ΔE = {d:.1f} ({where}, порог {limit})"
            elif vision is None:
                note = "контраст к фону: " + " · ".join(f"{contrast(c, THEME['background']):.1f}" for c in colors)
            else:
                note = ""
            ax.text(0, -0.38, note, ha="left", va="center", fontsize=11, color=THEME["text"])
    fig.suptitle("Палитра графиков: statlab/style.py", fontsize=16, weight="bold", x=0.08, ha="left")
    fig.text(0.08, 0.015,
             "Реальные данные рисуются цветом своей величины, модель, опорные линии и генератор - нейтральными. "
             "ΔE - расстояние в OKLab ×100, дальтонизм смоделирован по Machado et al. (2009).",
             fontsize=11, color=THEME["text"])
    fig.subplots_adjust(left=0.12, right=0.99, top=0.88, bottom=0.07, wspace=0.08, hspace=0.25)
    ASSETS.mkdir(exist_ok=True)
    fig.savefig(ASSETS / "palette.png", dpi=150, facecolor=THEME["background"])
    plt.close(fig)
    for group, swatches, pairs in GROUPS:
        if pairs:
            colors = [c for _, c in swatches]
            print(f"  {group}: " + ", ".join(f"{t} {worst_delta_e(colors, pairs, v):.1f}" for t, v in VISIONS))


# --- было / стало ------------------------------------------------------------------
CHARTS = [  # файл, подпись, фрагмент кода, по которому ячейка находится в обеих версиях ноутбука
    ("01_scatter", "1.2.2 · Ошибки двух функционалов по типам реакций", 'sns.scatterplot(data=df, x="e_r2", y="e_nn"'),
    ("02_delta", "1.3.1 · Распределение Δ и Δ по типам", 'df["delta"] = df.e_nn.abs() - df.e_r2.abs()'),
    ("03_tails", "1.4.2 · Хвосты распределений", "def gpd_tail("),
    ("04_generator", "2.1.4 · Данные и генератор Лапласа", '"Сравнение плотностей"'),
]


def chart_png(nb, marker):
    cells = [c for c in nb.cells if c.cell_type == "code" and marker in c.source]
    assert len(cells) == 1, marker
    outputs = [o for o in cells[0].outputs if "image/png" in o.get("data", {})]
    assert len(outputs) == 1, marker
    image = Image.open(io.BytesIO(base64.b64decode(outputs[0].data["image/png"]))).convert("RGB")
    width = outputs[0].get("metadata", {}).get("image/png", {}).get("width")
    if width and width < image.width:  # retina: приводим к логическому размеру, как в ноутбуке
        image = image.resize((width, round(image.height * width / image.width)), Image.LANCZOS)
    return image


def compose(caption, panels, max_side_by_side=1400):
    """Узкие графики ставятся рядом, широкие друг под другом."""
    font_path = font_manager.findfont(THEME["font"])
    big, small = ImageFont.truetype(font_path, 30), ImageFont.truetype(font_path, 24)
    side = sum(im.width for _, im in panels) + 40 * len(panels) <= max_side_by_side
    cells, x, y = [], 20, 80
    for label, im in panels:
        cells.append((label, im, x, y))
        if side:
            x += im.width + 40
        else:
            y += 56 + im.height
    content_w = max(cx + im.width for _, im, cx, _ in cells) + 20
    content_h = max(cy + 56 + im.height for _, im, _, cy in cells) + 20
    width = max(content_w, int(ImageDraw.Draw(Image.new("RGB", (1, 1))).textlength(caption, font=big)) + 40)
    sheet = Image.new("RGB", (width, content_h), THEME["background"])
    draw = ImageDraw.Draw(sheet)
    draw.text((20, 22), caption, font=big, fill=THEME["text"])
    for label, im, cx, cy in cells:
        draw.line([(cx, cy), (cx + im.width, cy)], fill=THEME["grid"], width=2)
        draw.text((cx, cy + 14), label, font=small, fill=THEME["text"])
        sheet.paste(im, (cx, cy + 56))
    return sheet


def build_before_after():
    from nbclient import NotebookClient

    source = subprocess.run(["git", "show", f"{BEFORE_COMMIT}:lab01.ipynb"], cwd=ROOT,
                            check=True, capture_output=True, text=True).stdout
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", nbformat.warnings.MissingIDFieldWarning)  # в старой версии нет id ячеек
        before = nbformat.reads(source, as_version=4)
    NotebookClient(before, timeout=900, kernel_name="python3",
                   resources={"metadata": {"path": str(ROOT)}}).execute()
    after = nbformat.read(ROOT / "lab01.ipynb", as_version=4)
    out = ASSETS / "before_after"
    out.mkdir(parents=True, exist_ok=True)
    for name, caption, marker in CHARTS:
        compose(caption, [(f"Было (коммит {BEFORE_COMMIT})", chart_png(before, marker)),
                          ("Стало", chart_png(after, marker))]).save(out / f"{name}.png")


# --- HTML-экспорт ------------------------------------------------------------------
def build_export():
    import plotly.io as pio
    from nbconvert import HTMLExporter

    EXPORT.mkdir(exist_ok=True)
    nb = nbformat.read(ROOT / "lab01.ipynb", as_version=4)
    first = True
    for cell in nb.cells:
        for output in cell.get("outputs", []):
            figure = output.get("data", {}).get("application/vnd.plotly.v1+json")
            if figure:
                figure = json.loads(json.dumps(figure))
                figure.pop("config", None)
                output.data["text/html"] = pio.to_html(figure, include_plotlyjs="cdn" if first else False,
                                                       full_html=False, validate=False)
                first = False
    exporter = HTMLExporter(exclude_input=True, exclude_input_prompt=True, exclude_output_prompt=True)
    html, _ = exporter.from_notebook_node(nb, resources={"metadata": {"name": "Сравнение r2SCAN и NN-r2SCAN"}})
    (EXPORT / "lab01.html").write_text(html, encoding="utf-8")
    subprocess.run([sys.executable, "-m", "marimo", "export", "html", str(HERE / "lab01_visual.py"),
                    "-o", str(EXPORT / "lab01_visual.html")], check=True)


STEPS = {"palette": build_palette, "before-after": build_before_after, "export": build_export}

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("steps", nargs="*", metavar="step", help=", ".join(STEPS))
    steps = parser.parse_args().steps or list(STEPS)
    if unknown := set(steps) - set(STEPS):
        parser.error(f"неизвестные шаги: {', '.join(sorted(unknown))}")
    for step in steps:
        print(step)
        STEPS[step]()
