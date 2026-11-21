import marimo

__generated_with = "0.25.2"
app = marimo.App(
    width="medium",
    app_title="Ошибки расчётных методов · GSCDB137",
    css_file="lab01_visual.css",
)


@app.cell(hide_code=True)
def _():
    import sys
    from pathlib import Path

    import marimo as mo
    import numpy as np
    import pandas as pd
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    from scipy import special, stats

    # Общая с основным ноутбуком палитра лежит в statlab/ в корне репозитория
    _root = str(Path(__file__).resolve().parent.parent)
    if _root not in sys.path:
        sys.path.insert(0, _root)
    from statlab.style import METHOD_COLORS, ROLE_COLORS, SEQUENTIAL, THEME, css_vars, style_chart

    return (
        METHOD_COLORS,
        Path,
        ROLE_COLORS,
        SEQUENTIAL,
        THEME,
        css_vars,
        go,
        make_subplots,
        mo,
        np,
        pd,
        special,
        stats,
        style_chart,
    )


@app.cell(hide_code=True)
def _(css_vars, mo):
    # Цвета и шрифт оформления страницы приходят из statlab/style.py через CSS-переменные
    chrome = css_vars()

    def section(number, title, anchor):
        return mo.Html(f'<h2 class="lab-section" id="{anchor}" style="{chrome}">{number} · {title}</h2>')

    mo.Html(f"""
    <header class="lab-hero" id="lab-top" style="{chrome}">
      <p>Лабораторная 01 · доп. задание КТвД</p>
      <h1>Ошибки расчётных методов</h1>
      <p>16 методов расчёта энергии реакций на базе GSCDB137. Выберите два и сравните, как они ошибаются.</p>
    </header>
    <details class="lab-nav" open style="{chrome}">
      <summary>Содержание</summary>
      <nav aria-label="Разделы">
        <a href="#lab-data">01 · Данные</a>
        <a href="#lab-random">02 · Почему ошибка случайная</a>
        <a href="#lab-eda">03 · Как распределены ошибки</a>
        <a href="#lab-dependence">04 · Связаны ли ошибки</a>
        <a href="#lab-generator">05 · Генератор</a>
        <a href="#lab-summary">06 · Выводы</a>
      </nav>
    </details>
    """)
    return chrome, section


@app.cell(hide_code=True)
def _(Path, pd):
    _gscdb = Path(__file__).resolve().parent.parent / "GSCDB-main"
    _types = (
        pd.read_csv(_gscdb / "Info" / "Datasets.csv")
        .dropna(subset=["Name"]).set_index("Name").Datatype_Short
    )
    all_rows = pd.read_csv(_gscdb / "Analysis" / "Results_errors.csv")
    all_rows["type"] = all_rows.Dataset.map(_types)
    # EF и FREQ - дипольные моменты, поляризуемости и частоты, а не энергии в ккал/моль
    _other_units = all_rows.type.isin(["EF", "FREQ"])
    excluded = all_rows[_other_units]
    errors = all_rows[~_other_units].reset_index(drop=True)
    methods = [c for c in all_rows.columns if c not in ("Reaction", "Dataset", "Reference", "type")]
    energy_types = ["BH", "TC", "ISO", "INC", "NC", "TM"]
    type_names = {
        "BH": "барьеры", "TC": "термохимия", "ISO": "изомеры",
        "INC": "взаимодействия внутри молекулы", "NC": "взаимодействия между молекулами",
        "TM": "переходные металлы",
    }
    return energy_types, errors, excluded, methods, type_names


@app.cell(hide_code=True)
def _(errors, excluded, methods, mo, section):
    method_a = mo.ui.dropdown(methods, value="B3LYP", label="Метод A")
    method_b = mo.ui.dropdown(methods, value="wB97M-V", label="Метод B")
    mo.vstack([
        section("01", "Данные", "lab-data"),
        mo.md(f"""
        Данные - опубликованные результаты базы GSCDB137 (Liang, Head-Gordon, 2025). Для каждой
        реакции известен точный ответ и ответы 16 расчётных методов (DFT-функционалов). Ошибка
        метода - насколько его ответ отличается от точного, в ккал/моль.

        Это не те данные, что в основном ноутбуке: там команда сама считала два метода на 861 реакции,
        а здесь опубликованные результаты 16 методов. Берём энергии реакций, их {len(errors)}.
        Ещё {len(excluded)} записей убрали: там другие величины в других единицах (дипольные моменты,
        частоты), и смешивать их с энергиями нельзя.
        """),
        mo.md(r"""
        Опыт - выбираем реакцию $\omega$ наугад. Ошибки двух методов на ней - две случайные величины:

        $$\varepsilon_A(\omega)=E_A(\omega)-E_\mathrm{ref}(\omega),\qquad
        \varepsilon_B(\omega)=E_B(\omega)-E_\mathrm{ref}(\omega).$$

        Выберите два метода - дальше вся страница сравнивает их ошибки.
        """),
        mo.hstack([method_a, method_b], justify="start", gap=2),
    ])
    return method_a, method_b


@app.cell(hide_code=True)
def _(METHOD_COLORS, errors, method_a, method_b, mo):
    names = {"A": method_a.value, "B": method_b.value}
    eps = {k: errors[name] for k, name in names.items()}
    # Роли те же, что у методов в основном ноутбуке: базовый (синий) и сравниваемый (оранжевый)
    colors = {"A": METHOD_COLORS["r2SCAN"], "B": METHOD_COLORS["NN-r2SCAN"]}
    mo.callout(mo.md("Выбран один и тот же метод. Выберите два разных."), kind="warn") \
        if names["A"] == names["B"] else None
    return colors, eps, names


@app.cell(hide_code=True)
def _(energy_types, eps, errors, mo, names, pd, section):
    def _spread(x):
        neighbours = x.groupby(errors.Dataset).transform("median")
        return {
            "Типичная ошибка, ккал/моль": x.abs().median(),
            "Типичное отличие от соседей по набору, ккал/моль": (x - neighbours).abs().median(),
        }

    spread = pd.DataFrame({f"{k}: {names[k]}": _spread(eps[k]) for k in ("A", "B")})
    random_type = mo.ui.dropdown(energy_types, value="BH", label="Тип реакций на графике")
    _typical, _diff = spread.iloc[:, 0]
    mo.vstack([
        section("02", "Почему ошибка случайная", "lab-random"),
        mo.md("""
        Похожие реакции собраны в наборы. Если бы ошибку определял набор, её можно было бы угадать
        заранее: у всех реакций набора она была бы одинаковой. Проверим, так ли это.
        """),
        mo.ui.table(spread.reset_index(names="Показатель").round(2), selection=None, show_download=False),
        mo.md(f"""
        У {names['A']} типичная ошибка {_typical:.2f} ккал/моль, а от соседей по набору она отличается
        на {_diff:.2f} ккал/моль. Даже зная набор, ошибку конкретной реакции не угадать, поэтому это
        случайная величина.

        На графике каждая строка - набор реакций. Чем шире разброс точек в строке, тем хуже набор
        предсказывает ошибку.
        """),
        random_type,
    ])
    return random_type, spread


@app.cell(hide_code=True)
def _(colors, eps, errors, go, mo, names, random_type, style_chart):
    _rows = errors.type == random_type.value
    _x, _sets = eps["A"][_rows], errors.Dataset[_rows]
    _order = _x.groupby(_sets).median().sort_values().index.tolist()
    _lo, _hi = _x.quantile([0.01, 0.99])
    _pad = 0.05 * (_hi - _lo)
    _fig = go.Figure(go.Box(
        x=_x, y=_sets, orientation="h", boxpoints="all", jitter=0.5, pointpos=0,
        marker=dict(color=colors["A"], size=4, opacity=0.45), line=dict(color=colors["A"], width=1),
        fillcolor="rgba(0,0,0,0)", customdata=errors.Reaction[_rows],
        hovertemplate="%{customdata}<br>ошибка %{x:.2f} ккал/моль<extra></extra>",
    ))
    style_chart(_fig, None, f"Ошибка {names['A']}, ккал/моль · показаны 98 % реакций", "Набор реакций")
    _fig.update_yaxes(categoryorder="array", categoryarray=_order)
    _fig.update_xaxes(range=[_lo - _pad, _hi + _pad])
    _fig.update_layout(height=140 + 22 * len(_order), showlegend=False)
    mo.ui.plotly(_fig)
    return


@app.cell(hide_code=True)
def _(eps, mo, names, pd, section):
    def _describe(x):
        return {
            "Реакций": len(x),
            "Средняя ошибка по модулю": x.abs().mean(),
            "Медиана": x.median(),
            "Разброс (стандартное отклонение)": x.std(),
            "Самая большая ошибка по модулю": x.abs().max(),
        }

    summary = pd.DataFrame({f"{k}: {names[k]}": _describe(eps[k]) for k in ("A", "B")})
    clip = mo.ui.dropdown(
        {"основную часть (98 % реакций)": 0.01, "почти все (99.8 %)": 0.001, "все реакции": 0.0},
        value="основную часть (98 % реакций)", label="Что показывать на графиках",
    )
    _largest = summary.loc["Самая большая ошибка по модулю"]
    mo.vstack([
        section("03", "Как распределены ошибки", "lab-eda"),
        mo.md("Ошибки в ккал/моль."),
        mo.ui.table(summary.reset_index(names="Показатель").round(2), selection=None, show_download=False),
        mo.md(f"""
        Большинство ошибок - несколько ккал/моль, но бывают редкие огромные: у {names['A']} до
        {_largest.iloc[0]:.0f}, у {names['B']} до {_largest.iloc[1]:.0f} ккал/моль. Поэтому графики
        по умолчанию показывают основную часть, а редкие большие ошибки - на последнем графике.
        """),
        clip,
    ])
    return clip, summary


@app.cell(hide_code=True)
def _(ROLE_COLORS, clip, colors, energy_types, eps, errors, go, mo, names, np, stats, style_chart):
    _both = np.concatenate([eps["A"], eps["B"]])
    _q = clip.value
    _lo, _hi = np.quantile(_both, [_q, 1 - _q])
    _note = f" · показаны {(1 - 2 * _q) * 100:g} % реакций" if _q else ""

    _edges = np.linspace(_lo, _hi, 121)
    _hist = go.Figure()
    for _k in ("A", "B"):
        _share = np.histogram(eps[_k], bins=_edges)[0] / len(eps[_k])
        _hist.add_scatter(x=_edges, y=np.r_[_share, _share[-1]], mode="lines", name=f"{_k}: {names[_k]}",
                          line=dict(shape="hv", color=colors[_k], width=2))
    style_chart(_hist, None, f"Ошибка, ккал/моль{_note}", "Доля реакций в интервале")
    _hist.update_xaxes(range=[_lo, _hi])
    _hist.update_yaxes(tickformat=".0%")

    _box = go.Figure([
        go.Box(x=errors.type, y=eps[_k], name=f"{_k}: {names[_k]}", offsetgroup=_k, boxpoints="outliers",
               marker=dict(color=colors[_k], size=3, opacity=0.4), line=dict(color=colors[_k], width=1.5))
        for _k in ("A", "B")
    ])
    _box.update_layout(boxmode="group")
    style_chart(_box, None, f"Тип реакций{_note}", "Ошибка, ккал/моль")
    _box.update_xaxes(categoryorder="array", categoryarray=energy_types)
    _box.update_yaxes(range=[_lo, _hi])

    _tail = go.Figure()
    for _k in ("A", "B"):
        _abs = np.sort(np.abs(eps[_k].to_numpy()))
        _abs = _abs[_abs > 0]
        _tail.add_scatter(x=_abs, y=1 - np.arange(len(_abs)) / len(_abs), mode="lines",
                          name=f"{_k}: {names[_k]}", line=dict(color=colors[_k], width=2))
    _sigma = eps["A"].std()
    _grid = np.geomspace(0.01, _sigma * 4.5, 200)
    _tail.add_scatter(x=_grid, y=2 * stats.norm.sf(_grid, scale=_sigma), mode="lines",
                      name="если бы ошибки A были нормальными",
                      line=dict(color=ROLE_COLORS["model"], dash="dash", width=1.5))
    style_chart(_tail, None, "Ошибка по модулю, ккал/моль, лог. шкала", "Доля реакций с ошибкой больше, лог. шкала")
    _tail.update_xaxes(type="log", dtick=1, exponentformat="power",
                       range=[-2, np.log10(np.abs(_both).max()) + 0.1])
    _tail.update_yaxes(type="log", dtick=1, exponentformat="power",
                       range=[np.log10(1 / len(eps["A"])), 0.05])

    mo.vstack([
        mo.ui.plotly(_hist),
        mo.ui.plotly(_box),
        mo.md("""
        Как часто встречаются большие ошибки. Пунктир показывает, как было бы при «обычном»
        (нормальном) распределении с тем же разбросом: там ошибок больше нескольких десятков
        ккал/моль почти нет, а у реальных методов они встречаются.
        """),
        mo.ui.plotly(_tail),
    ])
    return


@app.cell(hide_code=True)
def _(eps, mo, pd, section, stats):
    _a, _b = eps["A"], eps["B"]
    _pearson, _spearman = stats.pearsonr(_a, _b), stats.spearmanr(_a, _b)
    _labels = ["Q1", "Q2", "Q3", "Q4"]
    quartiles = pd.crosstab(pd.qcut(_a, 4, labels=_labels), pd.qcut(_b, 4, labels=_labels))
    _chi2 = stats.chi2_contingency(quartiles)
    _p = [_pearson.pvalue, _spearman.pvalue, _chi2.pvalue]
    _tests = pd.DataFrame({
        "Способ": ["Корреляция Пирсона", "Корреляция Спирмена", "Критерий χ² по четвертям"],
        "Значение": [round(_pearson.statistic, 2), round(_spearman.statistic, 2), round(_chi2.statistic)],
        "p-value": ["< 1e-300" if p == 0 else f"{p:.0e}" for p in _p],
        "Вывод": ["связь есть" if p < 0.05 else "связи не видно" for p in _p],
    })
    dependent = all(p < 0.05 for p in _p)
    mo.vstack([
        section("04", "Связаны ли ошибки двух методов", "lab-dependence"),
        mo.md(f"""
        Если бы ошибки не были связаны, точки на графиках ниже лежали бы бесформенным облаком,
        а все 16 клеток таблицы четвертей были бы примерно одинаковыми (около {len(_a) / 16:.0f}).
        Проверяем тремя способами; связь считается найденной, если p-value меньше 0.05.
        """),
        mo.ui.table(_tests, selection=None, show_download=False),
        mo.md("Связь есть: на трудных реакциях ошибаются оба метода." if dependent else
              "Связь видна не всеми способами."),
        mo.accordion({"Как это считается": mo.md(r"""
        $$r=\frac{\sum_i (a_i-\bar a)(b_i-\bar b)}{\sqrt{\sum_i (a_i-\bar a)^2\,\sum_i (b_i-\bar b)^2}},\qquad
        \rho = r\ \text{по рангам},\qquad
        \chi^2=\sum_{i,j}\frac{(O_{ij}-E_{ij})^2}{E_{ij}},\quad E_{ij}=\frac{R_i C_j}{N}.$$

        Пирсон измеряет, насколько точки ложатся на прямую, Спирмен - насколько одна ошибка растёт
        вместе с другой, $\chi^2$ сравнивает таблицу четвертей с той, что была бы без связи.
        """)}),
    ])
    return dependent, quartiles


@app.cell(hide_code=True)
def _(
    ROLE_COLORS,
    SEQUENTIAL,
    THEME,
    clip,
    colors,
    energy_types,
    eps,
    errors,
    go,
    make_subplots,
    mo,
    names,
    np,
    quartiles,
    style_chart,
    type_names,
):
    _q = clip.value
    _scatter = make_subplots(rows=2, cols=3, horizontal_spacing=0.07, vertical_spacing=0.14,
                             subplot_titles=[f"{t} · {type_names[t]}" for t in energy_types])
    for _i, _t in enumerate(energy_types):
        _row, _col = _i // 3 + 1, _i % 3 + 1
        _m = errors.type == _t
        _lo, _hi = np.quantile(np.concatenate([eps["A"][_m], eps["B"][_m]]), [_q, 1 - _q])
        _scatter.add_scatter(
            x=eps["A"][_m], y=eps["B"][_m], mode="markers", row=_row, col=_col, showlegend=False,
            marker=dict(color=colors["A"], size=4, opacity=0.35), customdata=errors.Reaction[_m],
            hovertemplate="%{customdata}<br>A: %{x:.2f}<br>B: %{y:.2f} ккал/моль<extra></extra>",
        )
        _scatter.add_scatter(x=[_lo, _hi], y=[_lo, _hi], mode="lines", row=_row, col=_col, showlegend=False,
                             line=dict(color=ROLE_COLORS["reference"], dash="dash", width=1), hoverinfo="skip")
        _scatter.update_xaxes(range=[_lo, _hi], row=_row, col=_col)
        _scatter.update_yaxes(range=[_lo, _hi], row=_row, col=_col)
    style_chart(_scatter, None, None, None)
    _scatter.update_layout(height=640, margin=dict(t=48))
    _scatter.update_annotations(font=dict(size=THEME["font_size"] - 1))
    for _col in (1, 2, 3):
        _scatter.update_xaxes(title_text=f"Ошибка {names['A']}", row=2, col=_col)
    for _row in (1, 2):
        _scatter.update_yaxes(title_text=f"Ошибка {names['B']}", row=_row, col=1)

    _z = quartiles.to_numpy()
    _heat = go.Figure(go.Heatmap(
        z=_z, x=quartiles.columns.astype(str), y=quartiles.index.astype(str), showscale=False,
        colorscale=[[i / (len(SEQUENTIAL) - 1), c] for i, c in enumerate(SEQUENTIAL)],
        hovertemplate="A: %{y}, B: %{x}<br>%{z} реакций<extra></extra>",
    ))
    for (_i, _j), _v in np.ndenumerate(_z):
        _heat.add_annotation(x=quartiles.columns[_j], y=quartiles.index[_i], text=str(_v), showarrow=False,
                             font=dict(color="#ffffff" if _v > _z.max() / 2 else THEME["text"]))
    style_chart(_heat, None, f"Четверть по ошибке {names['B']}", f"Четверть по ошибке {names['A']}")
    _heat.update_layout(height=420, width=520)

    mo.vstack([
        mo.md("""
        Каждая точка - реакция: по горизонтали ошибка A, по вертикали ошибка B, в ккал/моль. Пунктир -
        где ошибки равны. Типы реакций на отдельных панелях, потому что масштаб ошибок у них разный.
        """),
        mo.ui.plotly(_scatter),
        mo.md("""
        Реакции разбиты на четыре равные части по ошибке каждого метода: от самых отрицательных (Q1)
        до самых положительных (Q4). Тёмные клетки на диагонали значат, что методы чаще ошибаются
        в одну сторону.
        """),
        mo.ui.plotly(_heat),
    ])
    return


@app.cell(hide_code=True)
def _(mo, names, section):
    gen_variable = mo.ui.dropdown({f"{names['A']} (A)": "A", f"{names['B']} (B)": "B"},
                                  value=f"{names['A']} (A)", label="Чьи ошибки повторять")
    gen_dist = mo.ui.dropdown(["Нормальное", "Лапласа", "Коши", "Стьюдента"], value="Лапласа",
                              label="Распределение")
    mo.vstack([
        section("05", "Генератор случайных чисел", "lab-generator"),
        mo.md("""
        Генератор придумывает новые ошибки, похожие на настоящие. Выберите распределение - его
        параметры подберутся по данным автоматически, дальше их можно двигать ползунками.
        """),
        mo.hstack([gen_variable, gen_dist], justify="start", gap=2),
        mo.accordion({"Как работает генератор": mo.md(r"""
        Берём случайное число $U$ от 0 до 1 и пересчитываем его через обратную функцию выбранного
        распределения: $X = F^{-1}(U)$. Тогда $P(X \le x) = P(U \le F(x)) = F(x)$, то есть у $X$
        нужное распределение (метод обратной функции). Формула для выбранного распределения - под
        графиком.
        """)}),
    ])
    return gen_dist, gen_variable


@app.cell(hide_code=True)
def _(eps, gen_dist, gen_variable, mo, np, stats):
    gen_data = eps[gen_variable.value].to_numpy()
    _family = {"Нормальное": stats.norm, "Лапласа": stats.laplace, "Коши": stats.cauchy, "Стьюдента": stats.t}
    _fit = _family[gen_dist.value].fit(gen_data)
    _df, (_loc, _scale) = (_fit[0], _fit[1:]) if gen_dist.value == "Стьюдента" else (None, _fit)
    _iqr = np.subtract(*np.quantile(gen_data, [0.75, 0.25]))

    def _slider(start, stop, value, label, steps=200):
        step = (stop - start) / steps
        return mo.ui.slider(start, stop, step=step, value=start + round((value - start) / step) * step,
                            label=label, show_value=True, debounce=True)

    loc_slider = _slider(_loc - _iqr, _loc + _iqr, _loc, "Центр")
    scale_slider = _slider(_scale / 5, _scale * 5, _scale, "Ширина")
    df_slider = _slider(0.5, 30, _df, "Толщина хвостов ν", steps=295) if _df is not None else None
    sample_size = mo.ui.slider(500, 20000, step=500, value=round(len(gen_data) / 500) * 500,
                               label="Сколько чисел", show_value=True, debounce=True)
    seed = mo.ui.number(0, 2**31 - 1, step=1, value=42, label="Seed")
    mo.hstack([loc_slider, scale_slider, *([df_slider] if df_slider is not None else []), sample_size, seed],
              justify="start", wrap=True, gap=2)
    return df_slider, gen_data, loc_slider, sample_size, scale_slider, seed


@app.cell(hide_code=True)
def _(
    ROLE_COLORS,
    colors,
    df_slider,
    gen_data,
    gen_dist,
    gen_variable,
    go,
    loc_slider,
    mo,
    names,
    np,
    pd,
    sample_size,
    scale_slider,
    seed,
    special,
    stats,
    style_chart,
):
    _dist, _loc, _scale = gen_dist.value, loc_slider.value, scale_slider.value
    _df = df_slider.value if df_slider is not None else None
    _k = gen_variable.value

    def _inverse_cdf(u):
        if _dist == "Нормальное":
            return _loc + _scale * special.ndtri(u)
        if _dist == "Лапласа":
            return _loc - _scale * np.sign(u - 0.5) * np.log(1 - 2 * np.abs(u - 0.5))
        if _dist == "Коши":
            return _loc + _scale * np.tan(np.pi * (u - 0.5))
        return _loc + _scale * stats.t.ppf(u, _df)

    _formulas = {
        "Нормальное": r"X = \mu + \sigma\,\Phi^{-1}(U)",
        "Лапласа": r"X = \mu - b\,\operatorname{sign}\!\left(U - \tfrac12\right)\ln\!\left(1 - 2\left|U - \tfrac12\right|\right)",
        "Коши": r"X = x_0 + \gamma\,\tan\!\left(\pi\left(U - \tfrac12\right)\right)",
        "Стьюдента": r"X = \mu + s\,t_\nu^{-1}(U)",
    }
    _model = {
        "Нормальное": lambda: stats.norm(_loc, _scale), "Лапласа": lambda: stats.laplace(_loc, _scale),
        "Коши": lambda: stats.cauchy(_loc, _scale), "Стьюдента": lambda: stats.t(_df, _loc, _scale),
    }[_dist]()
    _tiny = np.finfo(float).eps
    _u = np.clip(np.random.default_rng(int(seed.value)).random(int(sample_size.value)), _tiny, 1 - _tiny)
    _generated = _inverse_cdf(_u)

    _lo, _hi = np.quantile(gen_data, [0.01, 0.99])
    _edges = np.linspace(_lo, _hi, 101)
    _grid = np.linspace(_lo, _hi, 400)
    _chart = go.Figure()
    for _values, _name, _color, _dash in [(gen_data, f"Данные: {names[_k]}", colors[_k], "solid"),
                                          (_generated, "Генератор", ROLE_COLORS["generator"], "dash")]:
        _share = np.histogram(_values, bins=_edges)[0] / len(_values)
        _chart.add_scatter(x=_edges, y=np.r_[_share, _share[-1]], mode="lines", name=_name,
                           line=dict(shape="hv", color=_color, dash=_dash, width=2))
    _model_name = {"Нормальное": "нормальное", "Лапласа": "Лапласа", "Коши": "Коши", "Стьюдента": "Стьюдента"}[_dist]
    _chart.add_scatter(x=_grid, y=_model.pdf(_grid) * np.diff(_edges)[0], mode="lines",
                       name=f"Распределение {_model_name}", line=dict(color=ROLE_COLORS["model"], width=2))
    style_chart(_chart, None, "Ошибка, ккал/моль · показаны 98 % реакций", "Доля значений в интервале")
    _chart.update_xaxes(range=[_lo, _hi])
    _chart.update_yaxes(tickformat=".0%")

    def _sample_stats(x):
        return [np.median(x), *np.quantile(x, [0.05, 0.95]), np.mean(np.abs(x) > 10)]

    _table = pd.DataFrame({
        "Показатель": ["Медиана, ккал/моль", "5 % значений меньше, ккал/моль", "5 % значений больше, ккал/моль",
                       "Доля ошибок больше 10 ккал/моль по модулю"],
        "Данные": np.round(_sample_stats(gen_data), 3),
        "Генератор": np.round(_sample_stats(_generated), 3),
    })
    _distance = stats.ks_2samp(gen_data, _generated).statistic
    mo.vstack([
        mo.ui.plotly(_chart),
        mo.md(f"Формула генератора:\n\n$${_formulas[_dist]}$$"),
        mo.ui.table(_table, selection=None, show_download=False),
        mo.md(f"""
        Насколько генератор похож на данные: D = {_distance:.3f} (критерий Колмогорова-Смирнова).
        Это самое большое расхождение между ними: 0 - полное совпадение, 1 - ничего общего.
        Переключите распределение и найдите то, где D меньше.
        """),
    ])
    return


@app.cell(hide_code=True)
def _(chrome, dependent, mo, names, section, spread, summary):
    _mae = summary.loc["Средняя ошибка по модулю"]
    _largest = summary.loc["Самая большая ошибка по модулю"]
    _typical = spread.loc["Типичная ошибка, ккал/моль"]
    _better, _worse = ("A", "B") if _mae.iloc[0] <= _mae.iloc[1] else ("B", "A")
    _i = {"A": 0, "B": 1}
    mo.vstack([
        section("06", "Выводы", "lab-summary"),
        mo.md(f"""
        Выводы пересчитываются при выборе других методов.

        - Ошибку метода нельзя предсказать заранее: даже среди похожих реакций одного набора она
          сильно меняется. Поэтому это случайная величина.
        - Обычно методы ошибаются немного (типичная ошибка {_typical.iloc[0]:.1f} и
          {_typical.iloc[1]:.1f} ккал/моль), но изредка очень сильно - до {_largest.max():.0f} ккал/моль.
        - {"Ошибки двух методов связаны: на трудных реакциях ошибаются оба." if dependent else
           "Связь между ошибками двух методов видна не всеми способами."}
        - {names[_better]} в среднем точнее: средняя ошибка {_mae.iloc[_i[_better]]:.1f} ккал/моль
          против {_mae.iloc[_i[_worse]]:.1f} у {names[_worse]}.

        Источник данных: Liang J., Head-Gordon M. Gold-Standard Chemical Database 137 (GSCDB137) //
        J. Chem. Theory Comput. 2025. Vol. 21, № 24. P. 12601-12621.
        [doi:10.1021/acs.jctc.5c01380](https://doi.org/10.1021/acs.jctc.5c01380)
        """),
        mo.Html(f'<p class="lab-back" style="{chrome}"><a href="#lab-top">↑ К содержанию</a></p>'),
    ])
    return


if __name__ == "__main__":
    app.run()
