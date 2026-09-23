"""
MSBA 325 - Streamlit Activity
Measles in Lebanon: drilling into the 2018 outbreak

Builds on my Plotly assignment (same MOPH dataset, same governorate colours).
Two linked controls:
  1. a time-window slider (months)
  2. a governorate focus dropdown whose options are re-ranked and relabelled
     with case counts for whatever window is selected in (1)

Author: Karim Chaar
Data: Lebanon Ministry of Public Health (MOPH) surveillance, via the
      AUB Linked Data Cube Portal (https://linked.aub.edu.lb:8502/)
"""

from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

DATA_PATH = Path(__file__).parent / "data" / "measles_lebanon_moph.csv"

# same colour per governorate as in the Plotly assignment, so both projects read the same
GOV_COLORS = {
    "Beqaa": "#B3122A",
    "Mount Lebanon": "#2F3C7E",
    "North Lebanon": "#5C8CA8",
    "Beirut": "#C98A3B",
    "South": "#5B8266",
    "Nabatieh": "#8C7AA9",
}
GOVS = list(GOV_COLORS)
CONTEXT_GREY = "#C9CCD1"
INK = "#2B2B2B"
MUTED = "#6B6F76"
ALL = "All of Lebanon"

# the raw export uses dbpedia-style names; the 2025 rows also renamed the North
NAME_MAP = {
    "Beqaa_Governorate": "Beqaa",
    "Mount_Lebanon_Governorate": "Mount Lebanon",
    "North_Lebanon_Governorate": "North Lebanon",
    "North_Governorate": "North Lebanon",
    "Beirut": "Beirut",
    "South_Governorate": "South",
    "Nabatieh_Governorate": "Nabatieh",
}

st.set_page_config(
    page_title="Measles in Lebanon | Outbreak explorer",
    page_icon="🦠",
    layout="wide",
)


# ------------------------------------------------------------------
# Data
# ------------------------------------------------------------------
@st.cache_data
def load_data(path: Path) -> pd.DataFrame:
    """Clean the linked-data export into one row per governorate-month."""
    raw = pd.read_csv(path)
    raw = raw[raw["refArea"].notna()].copy()  # one leftover RDF pointer row, not an observation

    df = pd.DataFrame({
        "governorate": raw["refArea"].str.split("/").str[-1].map(NAME_MAP),
        "period": raw["refPeriod"].str.split("/").str[-1],
        "cases": raw["Number of cases"].astype(int),
    })
    df["date"] = pd.to_datetime(df["period"], format="%m-%Y")
    return df[["governorate", "date", "cases"]].sort_values(["date", "governorate"])


def full_grid(df: pd.DataFrame) -> pd.DataFrame:
    """Governorate x month grid for 2015-2018. Months never reported stay NaN
    (South Governorate, all of 2016) so missing is never mistaken for zero."""
    core = df[df["date"].dt.year.between(2015, 2018)]
    grid = core.pivot_table(index="date", columns="governorate", values="cases", aggfunc="sum")
    months = pd.date_range("2015-01-01", "2018-12-01", freq="MS")
    return grid.reindex(index=months, columns=GOVS)


df = load_data(DATA_PATH)
grid = full_grid(df)
MONTHS = [d.strftime("%Y-%m") for d in grid.index]  # plain strings: select_slider round-trips these safely
national = grid.sum(axis=1, min_count=1)


def fmt_month(ts: pd.Timestamp) -> str:
    return ts.strftime("%b %Y")


def fmt_window(start: pd.Timestamp, end: pd.Timestamp) -> str:
    return fmt_month(start) if start == end else f"{fmt_month(start)} – {fmt_month(end)}"


# ------------------------------------------------------------------
# Session state + guided presets
# ------------------------------------------------------------------
PRESETS = {
    "full": ((MONTHS[0], MONTHS[-1]), ALL),
    "spring": (("2018-02", "2018-07"), "Beqaa"),
    "north": (("2018-09", "2018-12"), "North Lebanon"),
}


def apply_preset(name: str) -> None:
    # runs as a callback, i.e. *before* the widgets are drawn on the rerun,
    # which is the only point where Streamlit lets you overwrite widget state
    window, focus = PRESETS[name]
    st.session_state["window"] = window
    st.session_state["focus"] = focus


# ------------------------------------------------------------------
# Header + context
# ------------------------------------------------------------------
st.title("Measles in Lebanon: where and when did the 2018 outbreak hit?")
st.markdown(
    "Monthly measles cases reported by Lebanon's **Ministry of Public Health** for its six "
    "governorates, **January 2015 – December 2018** (plus a January–May 2025 snapshot). "
    "In my Plotly assignment I showed *that* 2018 was an outbreak year and that Beqaa carried "
    "most of it. This page lets you **zoom into any stretch of months and drill down into one "
    "governorate** to see how the outbreak actually moved."
)

with st.expander("About the data and how to read it"):
    st.markdown(
        """
- **Source:** MOPH Epidemiological Surveillance Unit, published as linked data on the
  [AUB Linked Data Cube Portal](https://linked.aub.edu.lb:8502/). 306 governorate-month observations.
- **What a number means:** *reported* cases, not total infections. Counts are **not adjusted for
  population**, so a large governorate will tend to report more cases. Compare shapes and timing
  more than raw size.
- **Missing data:** South Governorate has **no records for 2016**. Those months show as blank
  cells, not zeros, and the national total for 2016 covers only five governorates.
- **Cleaning:** one non-observation row from the RDF export was dropped; governorate and month
  were parsed from the linked-data URLs; "North Governorate" (2025 rows) was merged with
  "North Lebanon Governorate".
- **Why measles matters:** it is one of the most contagious diseases known, so a small drop in
  vaccination coverage can turn a handful of cases into an outbreak within weeks.
        """
    )

# ------------------------------------------------------------------
# Insights (author-driven) with "show me" buttons that set the controls
# ------------------------------------------------------------------
st.subheader("Three things the data shows")
i1, i2, i3 = st.columns(3)

beqaa_spring = grid.loc["2018-02":"2018-07", "Beqaa"].sum()
beqaa_total = grid["Beqaa"].sum()
spring_nat = national.loc["2018-02":"2018-07"].sum()
north_nd = grid.loc["2018-11":"2018-12", "North Lebanon"].sum()
nat_nd = national.loc["2018-11":"2018-12"].sum()

with i1:
    with st.container(border=True):
        st.markdown("**1 · A six-month outbreak, concentrated in one place**")
        st.markdown(
            f"Beqaa reported **{beqaa_spring:.0f} of its {beqaa_total:.0f} cases** from 2015 to 2018 "
            f"(**{beqaa_spring / beqaa_total:.0%}**) between February and July 2018, which was "
            f"**{beqaa_spring / spring_nat:.0%}** of every case in Lebanon during those months."
        )
        st.button("Show me the spring 2018 outbreak", on_click=apply_preset, args=("spring",),
                  width="stretch")
with i2:
    with st.container(border=True):
        st.markdown("**2 · It didn't end in summer. It moved north.**")
        st.markdown(
            f"National cases fell to **{national['2018-09-01']:.0f}** in September 2018, then rose "
            f"again. North Lebanon reported **{north_nd:.0f} cases in November–December**, "
            f"**{north_nd / nat_nd:.0%}** of the national total. A yearly chart hides this second wave."
        )
        st.button("Show me the northern wave", on_click=apply_preset, args=("north",),
                  width="stretch")
with i3:
    with st.container(border=True):
        cases_25 = df[df["date"].dt.year == 2025].groupby("governorate")["cases"].sum()
        st.markdown("**3 · The North is still the one to watch**")
        st.markdown(
            f"In the January–May 2025 snapshot, Lebanon reported **{cases_25.sum()} cases**. "
            f"North Lebanon had the most (**{cases_25.get('North Lebanon', 0)}**), even though Beqaa "
            "was the centre in 2018. The numbers are small, but the North is the last place "
            "where cases were still rising at the end of the outbreak."
        )
        st.button("Reset to the full 2015–2018 view", on_click=apply_preset, args=("full",),
                  width="stretch")

st.divider()

# ------------------------------------------------------------------
# Controls (reader-driven). Control 2 depends on control 1.
# ------------------------------------------------------------------
st.subheader("Explore it yourself")
c1, c2 = st.columns([3, 2], gap="large")

with c1:
    start, end = st.select_slider(
        "① Time window: drag either end to zoom into a period",
        options=MONTHS,
        format_func=lambda m: fmt_month(pd.Timestamp(m)),
        value=PRESETS["full"][0],  # a tuple here is what makes it a two-handle range slider
        key="window",
    )
start, end = pd.Timestamp(start), pd.Timestamp(end)

win = grid.loc[start:end]
win_national = win.sum(min_count=1).sum()
gov_totals = win.sum(min_count=1)                      # NaN if a governorate has no data at all in the window
gov_missing = win.isna().sum()                         # months with no record, per governorate
ranked = gov_totals.fillna(-1).sort_values(ascending=False).index.tolist()


def focus_label(option: str) -> str:
    """Dropdown labels are recomputed for the current window, so the list
    itself works as a ranking of where the cases were."""
    if option == ALL:
        return f"{ALL}: {win_national:.0f} cases"
    if pd.isna(gov_totals[option]):
        return f"{option}: no data for this window"
    share = gov_totals[option] / win_national if win_national else 0
    flag = " (some months missing)" if gov_missing[option] else ""
    n = gov_totals[option]
    return f"{option}: {n:.0f} case{'' if n == 1 else 's'} · {share:.0%}{flag}"


with c2:
    focus = st.selectbox(
        f"② Focus on a governorate (ranked by cases in {fmt_window(start, end)})",
        options=[ALL] + ranked,
        format_func=focus_label,
        key="focus",
    )

# ------------------------------------------------------------------
# KPI row
# ------------------------------------------------------------------
series = national if focus == ALL else grid[focus]
win_series = series.loc[start:end]
focus_cases = win_series.sum(min_count=1)

# same-length window one year earlier, when it exists and is complete, for context
prev_start, prev_end = start - pd.DateOffset(years=1), end - pd.DateOffset(years=1)
prev_cases = None
if prev_start >= grid.index[0] and (end - start).days < 366:
    prev_slice = series.loc[prev_start:prev_end]
    if prev_slice.notna().all():
        prev_cases = prev_slice.sum()

k1, k2, k3, k4 = st.columns(4)
k1.metric(
    f"Reported cases, {focus}",
    "no data" if pd.isna(focus_cases) else f"{focus_cases:,.0f}",
    delta=None if prev_cases is None or pd.isna(focus_cases) else f"{focus_cases - prev_cases:+,.0f} vs. same months a year earlier",
    delta_color="inverse",
)
if win_series.notna().any():
    k2.metric("Worst month in window", fmt_month(win_series.idxmax()), f"{win_series.max():.0f} cases",
              delta_color="off", delta_arrow="off")
else:
    k2.metric("Worst month in window", "–")
if focus == ALL:
    top = ranked[0]
    k3.metric("Largest contributor", top,
              f"{gov_totals[top] / win_national:.0%} of cases" if win_national else None, delta_color="off", delta_arrow="off")
else:
    k3.metric(f"{focus}'s share of national cases",
              "–" if pd.isna(focus_cases) or not win_national else f"{focus_cases / win_national:.0%}")
k4.metric("Governorates reporting ≥1 case", f"{int((gov_totals > 0).sum())} of 6")

# ------------------------------------------------------------------
# Chart 1: full timeline for context, selected window shaded, focus highlighted
# ------------------------------------------------------------------
BASE_LAYOUT = dict(
    template="plotly_white",
    font=dict(family="Arial", size=13, color=INK),
    title_font=dict(size=16),
    margin=dict(l=10, r=10, t=60, b=10),
    hoverlabel=dict(bgcolor="white", font_size=13),
)

fig_line = go.Figure()
is_full_window = (start, end) == (grid.index[0], grid.index[-1])
if not is_full_window:  # shading everything would just tint the whole chart
    fig_line.add_vrect(x0=start - pd.Timedelta(days=14), x1=end + pd.Timedelta(days=14),
                       fillcolor="#F2D4D8", opacity=0.45, line_width=0, layer="below")
fig_line.add_trace(go.Scatter(
    x=national.index, y=national.values, name="All of Lebanon",
    mode="lines", line=dict(color=INK if focus == ALL else CONTEXT_GREY, width=2.5 if focus == ALL else 2),
    hovertemplate="%{x|%b %Y}<br>Lebanon: <b>%{y:.0f}</b> cases<extra></extra>",
))
if focus != ALL:
    fig_line.add_trace(go.Scatter(
        x=grid.index, y=grid[focus], name=focus, mode="lines+markers",
        line=dict(color=GOV_COLORS[focus], width=2.5), marker=dict(size=6),
        connectgaps=False,
        hovertemplate="%{x|%b %Y}<br>" + focus + ": <b>%{y:.0f}</b> cases<extra></extra>",
    ))
if win_series.notna().any():
    pk = win_series.idxmax()
    fig_line.add_annotation(x=pk, y=win_series.max(), text=f"{fmt_month(pk)}: {win_series.max():.0f}",
                            showarrow=True, arrowhead=0, ax=0, ay=-28, font=dict(color=INK, size=12))

focus_name = "Lebanon" if focus == ALL else focus
fig_line.update_layout(
    **BASE_LAYOUT, height=340,
    title=f"{focus_name}, monthly cases 2015–2018" + ("" if is_full_window else f" · shaded area = your window ({fmt_window(start, end)})"),
    legend=dict(orientation="h", yanchor="bottom", y=1.0, x=1, xanchor="right"),
    yaxis=dict(title="Reported cases", gridcolor="#EEEEEE", rangemode="tozero"),
    xaxis=dict(showgrid=False),
    hovermode="x unified",
)
if focus == "South":
    fig_line.add_annotation(x="2016-07-01", y=0, yshift=12, showarrow=False,
                            text="no South data in 2016", font=dict(color=MUTED, size=11))
st.plotly_chart(fig_line, width="stretch")

# ------------------------------------------------------------------
# Chart 2 (where) + Chart 3 (where x when) for the selected window
# ------------------------------------------------------------------
left, right = st.columns([2, 3], gap="large")

with left:
    bars = gov_totals.reindex(ranked[::-1])  # reversed so the biggest bar ends up on top
    colors = [GOV_COLORS[g] if focus in (ALL, g) else CONTEXT_GREY for g in bars.index]
    labels = [
        "no data" if pd.isna(v) else f"{v:.0f} ({v / win_national:.0%})" if win_national else f"{v:.0f}"
        for v in bars.values
    ]
    fig_bar = go.Figure(go.Bar(
        x=bars.fillna(0).values, y=bars.index, orientation="h",
        marker=dict(color=colors, cornerradius=4), text=labels, textposition="outside",
        cliponaxis=False,
        hovertemplate="%{y}: <b>%{x:.0f}</b> cases<extra></extra>",
    ))
    top_gov = ranked[0]
    bar_title = (
        f"{top_gov} had the most cases in this window"
        if win_national else "No cases reported in this window"
    )
    fig_bar.update_layout(
        **BASE_LAYOUT, height=380, title=bar_title, showlegend=False,
        xaxis=dict(title="Reported cases in window", showgrid=False, showticklabels=False, zeroline=False,
                   range=[0, max(bars.max(skipna=True) or 1, 1) * 1.35]),
        yaxis=dict(showgrid=False),
    )
    st.plotly_chart(fig_bar, width="stretch")

with right:
    heat = win.T.reindex(GOVS)
    xlabels = [d.strftime("%b %y") for d in heat.columns]
    hover_txt = heat.map(lambda v: "no data" if pd.isna(v) else f"{v:.0f} cases")
    fig_heat = go.Figure(go.Heatmap(
        z=heat.values, x=xlabels, y=heat.index, colorscale="Reds", zmin=0,
        xgap=1, ygap=2, customdata=hover_txt.values,
        colorbar=dict(title="Cases", thickness=12),
        hovertemplate="%{y} · %{x}<br><b>%{customdata}</b><extra></extra>",
    ))
    if focus != ALL:
        row = GOVS.index(focus)
        fig_heat.add_shape(type="rect", xref="x", yref="y", x0=-0.5, x1=len(xlabels) - 0.5,
                           y0=row - 0.5, y1=row + 0.5, line=dict(color=INK, width=2))
    step = max(1, len(xlabels) // 12)
    fig_heat.update_layout(
        **BASE_LAYOUT, height=380,
        title="When and where: each cell is one governorate-month (blank = not reported)",
        xaxis=dict(tickangle=-45, tickmode="array", tickvals=xlabels[::step], showgrid=False),
        yaxis=dict(autorange="reversed", showgrid=False),
    )
    st.plotly_chart(fig_heat, width="stretch")

with st.expander("See the numbers behind the charts"):
    table = win.copy()
    table.index = table.index.strftime("%b %Y")
    table["All of Lebanon"] = table.sum(axis=1, min_count=1)
    st.dataframe(table.astype("Int64"), width="stretch")

st.divider()

# ------------------------------------------------------------------
# Design justifications
# ------------------------------------------------------------------
st.subheader("Design notes")
with st.expander("① Why a time-window slider?"):
    st.markdown(
        """
**User question.** *"How big was the outbreak during a particular stretch of months, and when did it peak?"*
For example, a reader can compare the spring 2018 surge with the smaller rise at the end of that year.

**Why this widget.** I used a range `select_slider` that snaps to the 48 months in the data. I also
considered two `date_input` calendars and a year dropdown. The calendars let you pick individual days
even though the data is monthly, they take two separate interactions, and they allow a start date after
the end date. A year dropdown was too coarse: the northern second wave happens *inside* 2018, so a
yearly filter would hide the second insight. The slider has one control with two handles and no
invalid states.

**Course concept: overview first, then zoom, while keeping context.** The top chart always shows the
full 2015–2018 timeline, and the chosen window is only *shaded* on it. The reader can zoom into a few
months without losing sight of how they compare with the calm years before. The bar chart and heatmap
below then show only that window. The KPI row also compares the window with the same months a year
earlier, so every number has a baseline.
        """
    )
with st.expander("② Why a ranked governorate dropdown, and how is it linked to the slider?"):
    st.markdown(
        """
**User question.** *"Which governorate drove the cases in this period, and how does its curve
compare with the national one?"*

**How it is linked.** The dropdown's options are **re-ranked and relabelled every time the slider
moves**. Each option shows that governorate's case count and share *for the current window*, so the
list itself is a ranking. Beqaa is on top for spring 2018, and North Lebanon moves to the top when
you slide to November–December. A governorate with no records in the window (South in 2016) is
labelled "no data" instead of "0". The slider sets the scope, and the dropdown drills into it. The
result (the highlighted line, bar and heatmap row, and the "share of national" KPI) depends on both.

**Why this widget.** I considered a `multiselect` and clicking on the bars. A multiselect invites
people to plot all six governorates as coloured lines, which becomes a spaghetti chart where no
line stands out. Clicking a bar is hard to discover and is not keyboard-friendly. A single-choice
`selectbox` also has room for the count and share inside each label, which radio buttons would make
crowded.

**Course concept: focus attention and reduce clutter.** Once a governorate is selected, it is the
only element drawn in colour (its colour from my Plotly assignment). Every other line and bar
becomes light grey, and its row in the heatmap gets an outline. Colour is used as a *preattentive*
cue: the eye goes to the focus first, and the grey context is still there for comparison without
competing for attention.
        """
    )

st.caption(
    "Built by Karim Chaar for MSBA 325 (AUB, Olayan School of Business). Data: Lebanon MOPH via the AUB "
    "Linked Data Cube Portal. Case counts are reported cases and are not population-adjusted."
)
