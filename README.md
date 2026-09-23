# Measles in Lebanon: 2018 Outbreak Explorer

**Live app:** https://karimchaar01-measles-streamlit-app-alq8ye.streamlit.app/

An interactive Streamlit page built on my MSBA 325 Plotly assignment. It uses monthly measles cases
reported by Lebanon's Ministry of Public Health (2015-2018, plus January-May 2025) and asks:
**where and when did the 2018 outbreak hit, and how did it move?**

## What the page shows
- **Context:** source, what the counts mean, missing data (South Governorate has no 2016 records).
- **Three insights:**
  1. Beqaa reported 85% of its 2015-2018 cases in just six months (Feb-Jul 2018).
  2. The outbreak did not end in the summer. It moved to North Lebanon, which reported 75% of national cases in Nov-Dec 2018.
  3. 2025 is back to normal nationally (20 cases in Jan-May), but North Lebanon is above every pre-outbreak year.
- **Five charts:** full-timeline line chart (window shaded), ranked bar chart, governorate x month
  heatmap, small multiples of each governorate's curve (timing of peaks), and a 2025 vs. pre-outbreak chart.

## The two linked interactions
1. **Time-window slider** (`st.select_slider`, range of months): sets the period for every chart and KPI.
2. **Governorate focus** (`st.selectbox`): its options are **re-ranked and relabelled with case counts
   for the window chosen in (1)**, so the dropdown works as a ranking. The chosen governorate is
   highlighted in colour and everything else turns grey.

The "Show me…" buttons under each insight set both controls at once, taking the reader straight to that view.

## Run locally
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Files
| File | Purpose |
|---|---|
| `app.py` | The Streamlit app |
| `data/measles_lebanon_moph.csv` | Raw export from the AUB Linked Data Cube Portal |
| `requirements.txt` | Pinned dependencies for Streamlit Community Cloud |
| `.streamlit/config.toml` | Page theme |

## Data source
Lebanon Ministry of Public Health, Epidemiological Surveillance Unit, via the
[AUB Linked Data Cube Portal](https://linked.aub.edu.lb:8502/). Counts are reported cases and are not
population-adjusted.

*Karim Chaar · MSBA 325, Olayan School of Business, AUB*
