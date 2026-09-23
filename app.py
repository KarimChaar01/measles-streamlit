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
from plotly.subplots import make_subplots
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

# shared look for every Plotly figure on the page
BASE_LAYOUT = dict(
    template="plotly_white",
    font=dict(family="Arial", size=13, color=INK),
    title_font=dict(size=16),
    margin=dict(l=10, r=10, t=60, b=10),
    hoverlabel=dict(bgcolor="white", font_size=13),
)

CHART_CONFIG = {"displayModeBar": False}  # hide the Plotly toolbar for a cleaner page

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
    return fmt_month(start) if start == end else f"{fmt_month(start)} to {fmt_month(end)}"


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
    "Monthly measles cases in Lebanon's six governorates, **2015-2018** plus **Jan-May 2025**, "
    "reported by the Ministry of Public Health. Pick a time window, then a governorate, to see "
    "where and when the outbreak hit."
)

with st.expander("About the data and how to read it"):
    st.markdown(
        """
- **Source:** MOPH Epidemiological Surveillance Unit, via the
  [AUB Linked Data Cube Portal](https://linked.aub.edu.lb:8502/). 306 governorate-months.
- **Counts** are *reported* cases and are **not population-adjusted**. Bigger governorates report more.
- **Missing:** South Governorate has **no 2016 data**. It is shown blank, not as zero.
- **Cleaning:** dropped one non-data row, parsed place and month from the URLs, and merged
  "North Governorate" (2025) into "North Lebanon Governorate".
- **Why it matters:** measles is extremely contagious, so a small gap in vaccination can become an
  outbreak within weeks.
        """
    )

# ------------------------------------------------------------------
# Insights (author-driven) with "show me" buttons that set the controls
# ------------------------------------------------------------------
st.subheader("Key insights")
INSIGHT_BOX_HEIGHT = 175  # same height for all three cards so the buttons line up
i1, i2, i3 = st.columns(3)

beqaa_spring = grid.loc["2018-02":"2018-07", "Beqaa"].sum()
beqaa_total = grid["Beqaa"].sum()
spring_nat = national.loc["2018-02":"2018-07"].sum()
north_nd = grid.loc["2018-11":"2018-12", "North Lebanon"].sum()
nat_nd = national.loc["2018-11":"2018-12"].sum()

with i1:
    with st.container(border=True, height=INSIGHT_BOX_HEIGHT):
        st.markdown("**1. Six months, one governorate**")
        st.markdown(
            f"**{beqaa_spring / beqaa_total:.0%}** of Beqaa's four-year total came in Feb-Jul 2018: "
            f"**{beqaa_spring / spring_nat:.0%}** of all cases in Lebanon in those months."
        )
        st.button("Show me", on_click=apply_preset, args=("spring",), key="btn_spring",
                  width="stretch")
with i2:
    with st.container(border=True, height=INSIGHT_BOX_HEIGHT):
        st.markdown("**2. It didn't end. It moved north.**")
        st.markdown(
            f"Cases fell to {national['2018-09-01']:.0f} in Sep 2018. Then North Lebanon surged: "
            f"**{north_nd:.0f} cases in Nov-Dec**, **{north_nd / nat_nd:.0%}** of the national total."
        )
        st.button("Show me", on_click=apply_preset, args=("north",), key="btn_north",
                  width="stretch")
with i3:
    with st.container(border=True, height=INSIGHT_BOX_HEIGHT):
        # 2025 only covers Jan-May, so compare it with Jan-May of the pre-outbreak years
        jan_may = df[df["date"].dt.month <= 5].assign(year=lambda d: d["date"].dt.year)
        jm = jan_may.pivot_table(index="governorate", columns="year", values="cases", aggfunc="sum").reindex(GOVS)
        pre = jm[[2015, 2016, 2017]]
        st.markdown("**3. 2025 is quiet, except in the North**")
        st.markdown(
            f"Jan-May 2025 had **{jm[2025].sum():.0f} cases**, a normal level. But North Lebanon's "
            f"**{jm.loc['North Lebanon', 2025]:.0f}** beats every pre-outbreak year "
            f"({', '.join(f'{v:.0f}' for v in pre.loc['North Lebanon'])})."
        )
        st.button("Reset view", on_click=apply_preset, args=("full",), key="btn_reset",
                  width="stretch")

with st.expander("Insight 3 chart: 2025 vs. pre-outbreak years"):
    order = pre.max(axis=1).sort_values().index
    fig_25 = go.Figure()
    fig_25.add_trace(go.Bar(  # grey bar spanning the 2015-2017 min..max for Jan-May
        y=order, x=pre.loc[order].max(axis=1) - pre.loc[order].min(axis=1), base=pre.loc[order].min(axis=1),
        orientation="h", marker=dict(color="#E3E5E8", cornerradius=4), width=0.45,
        name="Jan-May range, 2015-2017",
        customdata=pre.loc[order].apply(lambda r: ", ".join("n/a" if pd.isna(v) else f"{v:.0f}" for v in r), axis=1),
        hovertemplate="%{y}<br>2015, 2016, 2017: %{customdata}<extra></extra>",
    ))
    fig_25.add_trace(go.Scatter(
        y=order, x=jm.loc[order, 2025], mode="markers+text", name="Jan-May 2025",
        marker=dict(size=14, color=[GOV_COLORS[g] for g in order], line=dict(color="white", width=2)),
        text=[f"{v:.0f}" for v in jm.loc[order, 2025]], textposition="middle right",
        hovertemplate="%{y}<br>Jan-May 2025: <b>%{x:.0f}</b> cases<extra></extra>",
    ))
    fig_25.update_layout(
        **BASE_LAYOUT, height=320,
        title="North Lebanon is the only governorate above its pre-outbreak range in 2025",
        xaxis=dict(title="Reported cases, Jan-May", gridcolor="#EEEEEE", range=[-1.5, pre.max().max() + 3]),
        legend=dict(orientation="h", yanchor="bottom", y=1.0, x=1, xanchor="right"),
    )
    fig_25.update_traces(cliponaxis=False)
    st.plotly_chart(fig_25, width="stretch", config=CHART_CONFIG)
    st.caption("Grey = 2015-2017 range. 2018 left out (off the scale). Small numbers: an early signal, not an outbreak.")

st.divider()

# ------------------------------------------------------------------
# Controls (reader-driven). Control 2 depends on control 1.
# ------------------------------------------------------------------
st.subheader("Explore it yourself")
c1, c2 = st.columns([3, 2], gap="large")

with c1:
    start, end = st.select_slider(
        "Time window",
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
        f"Governorate, ranked by cases in {fmt_window(start, end)}",
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
    delta=None if prev_cases is None or pd.isna(focus_cases) else f"{focus_cases - prev_cases:+,.0f} vs. a year before",
    delta_color="inverse",
)
if win_series.notna().any():
    k2.metric("Peak month", fmt_month(win_series.idxmax()), f"{win_series.max():.0f} cases",
              delta_color="off", delta_arrow="off")
else:
    k2.metric("Peak month", "n/a")
if focus == ALL:
    top = ranked[0]
    k3.metric("Largest contributor", top,
              f"{gov_totals[top] / win_national:.0%} of cases" if win_national else None, delta_color="off", delta_arrow="off")
else:
    k3.metric("Share of national cases",
              "n/a" if pd.isna(focus_cases) or not win_national else f"{focus_cases / win_national:.0%}")
k4.metric("Governorates with cases", f"{int((gov_totals > 0).sum())} of 6")

# ------------------------------------------------------------------
# Chart 1: full timeline for context, selected window shaded, focus highlighted
# ------------------------------------------------------------------
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
    title=f"{focus_name}, monthly cases 2015-2018" + ("" if is_full_window else " (shaded: your window)"),
    legend=dict(orientation="h", yanchor="bottom", y=1.0, x=1, xanchor="right"),
    yaxis=dict(title="Reported cases", gridcolor="#EEEEEE", rangemode="tozero"),
    xaxis=dict(showgrid=False),
    hovermode="x unified",
)
if focus == "South":
    fig_line.add_annotation(x="2016-07-01", y=0, yshift=12, showarrow=False,
                            text="no South data in 2016", font=dict(color=MUTED, size=11))
st.plotly_chart(fig_line, width="stretch", config=CHART_CONFIG)

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
    st.plotly_chart(fig_bar, width="stretch", config=CHART_CONFIG)

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
        title="Cases by governorate and month (blank = no data)",
        xaxis=dict(tickangle=-45, tickmode="array", tickvals=xlabels[::step], showgrid=False),
        yaxis=dict(autorange="reversed", showgrid=False),
    )
    st.plotly_chart(fig_heat, width="stretch", config=CHART_CONFIG)

# ------------------------------------------------------------------
# Chart 4: small multiples, one panel per governorate on its own scale,
# so the *timing* of each outbreak can be compared regardless of its size
# ------------------------------------------------------------------
# overall 2015-2018 peak per governorate: fixed, so the timing story does not shift with the window
peaks = {g: (grid[g].idxmax(), grid[g].max()) for g in GOVS}
SM_MIN_SCALE = 10  # own scale per panel, but never below 0-10, so 2-3 case blips stay small
fig_sm = make_subplots(
    rows=2, cols=3, shared_xaxes=True, vertical_spacing=0.16, horizontal_spacing=0.05,
    subplot_titles=[f"<b>{g}</b> · peak {fmt_month(peaks[g][0])} ({peaks[g][1]:.0f})" for g in GOVS],
)
for i, g in enumerate(GOVS):
    r, c = divmod(i, 3)
    selected = focus == g
    dimmed = focus not in (ALL, g)
    fig_sm.add_trace(go.Scatter(
        x=grid.index, y=grid[g], mode="lines", connectgaps=False, opacity=0.45 if dimmed else 1,
        line=dict(color=GOV_COLORS[g], width=3.5 if selected else 2),
        hovertemplate="%{x|%b %Y}: <b>%{y:.0f}</b><extra>" + g + "</extra>",
    ), row=r + 1, col=c + 1)
    fig_sm.add_trace(go.Scatter(
        x=[peaks[g][0]], y=[peaks[g][1]], mode="markers", opacity=0.45 if dimmed else 1,
        marker=dict(size=9, color=GOV_COLORS[g], line=dict(color="white", width=2)), hoverinfo="skip",
    ), row=r + 1, col=c + 1)
    fig_sm.update_yaxes(range=[0, max(peaks[g][1], SM_MIN_SCALE) * 1.15], row=r + 1, col=c + 1)
    if not is_full_window:
        fig_sm.add_vrect(x0=start - pd.Timedelta(days=14), x1=end + pd.Timedelta(days=14),
                         fillcolor="#F2D4D8", opacity=0.45, line_width=0, layer="below",
                         row=r + 1, col=c + 1)
fig_sm.update_annotations(font=dict(size=13, color=INK))
fig_sm.update_yaxes(gridcolor="#EEEEEE", nticks=4)
fig_sm.update_xaxes(showgrid=False, dtick="M12", tickformat="%Y")
fig_sm.update_layout(
    **BASE_LAYOUT, height=460, showlegend=False,
    title="Did every governorate peak at the same time?",
)
st.plotly_chart(fig_sm, width="stretch", config=CHART_CONFIG)
st.caption(
    "Each panel has its own scale (at least 0-10), so compare timing, not height. Dot = 2015-2018 peak. "
    "Beqaa and Mount Lebanon peaked in May 2018, North Lebanon in December."
)

with st.expander("See the numbers behind the charts"):
    table = win.copy()
    table.index = table.index.strftime("%b %Y")
    table["All of Lebanon"] = table.sum(axis=1, min_count=1)
    st.dataframe(table.astype("Int64"), width="stretch")
    st.download_button(
        f"Download this window as CSV ({fmt_window(start, end)})",
        data=table.astype("Int64").to_csv(index_label="month").encode("utf-8"),
        file_name=f"measles_lebanon_{start:%Y-%m}_to_{end:%Y-%m}.csv",
        mime="text/csv",
    )

st.divider()

# ------------------------------------------------------------------
# Design justifications
# ------------------------------------------------------------------
st.subheader("Design notes")
with st.expander("Why a time-window slider?"):
    st.markdown(
        """
**User question.** When did the outbreak happen, and how big was it in a given period?
For example, the spring 2018 surge vs. the smaller rise at the end of the year.

**Why this widget.** A range `select_slider` snaps to the 48 months in the data: one control, two
handles, no invalid ranges. I considered two `date_input` calendars, but they allow single days on
monthly data and a start after the end. A year dropdown was too coarse: the northern wave happens
*inside* 2018, so it would hide insight 2.

**Course concept: context.** The top chart always shows the full 2015-2018 timeline and only
*shades* the chosen window, so zooming in never hides the calm years that make 2018 stand out.
The first KPI also compares the window with a year before, so each number has a baseline.
        """
    )
with st.expander("Why a ranked governorate dropdown, and how is it linked?"):
    st.markdown(
        """
**User question.** Which governorate drove the cases in this period, and how does its curve
compare with the national one?

**How it is linked.** Every time the slider moves, the dropdown is **re-ranked and relabelled**
with each governorate's cases and share in that window. Beqaa leads in spring 2018, North Lebanon
in Nov-Dec, and South in 2016 reads "no data", not 0. The slider sets the scope and the dropdown
drills into it. The "Show me" buttons set both at once.

**Why this widget.** A `multiselect` invites plotting all six lines at once (spaghetti). Clicking
on bars is hard to discover and not keyboard-friendly. A `selectbox` also fits the count and share
into each label, which radio buttons would make crowded.

**Course concept: focus attention, reduce clutter.** Only the chosen governorate keeps its colour.
Everything else turns grey, and its heatmap row gets an outline. Colour works as a *preattentive*
cue: the eye lands on the focus first, while the grey context stays available.
        """
    )
with st.expander("Why these charts (and no pie chart or animation)"):
    st.markdown(
        """
| Chart | Question | From Plotly? |
|---|---|---|
| Line chart, full timeline | When, compared with normal years? | Yes |
| Ranked bar chart | Where, in my window? | Yes |
| Heatmap | Where and when at once | Yes |
| Small multiples | Did everyone peak at the same time? | New |
| 2025 range-and-dot | Is it coming back? | New |

The first four respond to both controls. The 2025 chart is fixed because it covers a different period.

**No pie chart.** The bar labels already show each share (e.g. "516 (67%)"), and bar lengths are
easier to compare than slice angles.

**No animation.** The slider does the same job at the reader's pace, and the small multiples show
the whole sequence at once.

**Separate scales in the small multiples.** On a shared axis, Beqaa's 151-case peak would flatten
the North's wave. Separate scales leave only *timing* to compare, and the panel titles keep the
real peak numbers visible. Each scale is at least 0-10, so a 2-case blip in Nabatieh does not look like an outbreak.
        """
    )

st.caption(
    "Built by Karim Chaar for MSBA 325 (AUB, Olayan School of Business). Data: Lebanon MOPH via the AUB "
    "Linked Data Cube Portal. Case counts are reported cases and are not population-adjusted."
)
