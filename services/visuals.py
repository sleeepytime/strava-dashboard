# visuals.py

from services.analytics import build_grouped_metrics
from services.utils import format_pace

THEME = {
    "bg_color": "rgba(0,0,0,0)",
    "font_color": "#E0E0E0",
    "grid_color": "#2C2C30",
    "primary_color": "#FC5200", # strava orange
    "trend_color": "#00AAFC",   # complementary blue
    "hover_bg": "#242428",
}

def empty_figure(message):
    return {
        "data": [],
        "layout": {
            "paper_bgcolor": "#242428",
            "plot_bgcolor": "#242428",
            "font": {"color": "#E0E0E0"},
            "xaxis": {"visible": False},
            "yaxis": {"visible": False},
            "annotations": [{
                "text": message,
                "xref": "paper",
                "yref": "paper",
                "showarrow": False,
                "font": {"size": 16}
            }]
        }
    }

def build_chart_config(traces, y_title, reverse_y=False, tickvals=None, ticktext=None):
    """Standardizes the look of all charts on the dashboard."""
    return {
        "data": traces,
        "layout": {
            "paper_bgcolor": THEME["bg_color"],
            "plot_bgcolor": THEME["bg_color"],
            "font": {"color": THEME["font_color"]},
            "xaxis": {
                "gridcolor":THEME["grid_color"], 
                "type": "date", 
                "tickangle": -45,
                "automargin": True},
            "yaxis": {
                "title": y_title, 
                "gridcolor": THEME["grid_color"], 
                "autorange": "reversed" if reverse_y else True,
                "tickvals": tickvals,
                "ticktext": ticktext
            },
            "margin": {"t": 20, "b": 60, "l": 60, "r": 20},
            "hovermode": "closest",
            "hoverlabel": {
                "bgcolor": THEME["hover_bg"],  # Match your card background
                "font": {"color": THEME["font_color"], "size": 13},
                "bordercolor": "#444",
                "namelength": -1
            },
            "transition": {
                "duration": 500,
                "easing": "cubic-in-out"
            },
            "frame": {"duration": 500},
            "showlegend": True,
            "legend": {
                "x": 1.02,
                "y": 0.5
            }
        }
    }

def make_trace(x, y, name, mode="markers", color=None):
    """Uses THEME colors if no specific color is provided"""
    color = color or THEME["primary_color"]

    trace = {
        "x": x,
        "y": y,
        "name": name,
        "meta": name,
        "type": "scatter",
        "mode": mode,
        "marker": {
            "color": color,
            "size": 8 if mode == "markers" else 0,
            "opacity": 0.7
        },
        "line": {
            "color": color,
            "width": 3,
            "shape": "spline",
            "smoothing": 1.3 if mode == "lines" else {},
        },
        "hoverinfo": "none"
    }

    if mode == "markers":
        trace["selected"] = {"marker": {"opacity": 1, "size": 12}}
        trace["unselected"] = {"marker": {"opacity": 0.2}}         # Others fade
    
    return trace

def get_graphs(df):
    if df.empty:
        return {"mile_chart": empty_figure("No Data"), "pace_chart": empty_figure("No Data")}

    # 1. Get the smoothed math (from your existing build_grouped_metrics)
    grouped = build_grouped_metrics(df)

    # 2. Build Miles Traces
    m_raw = make_trace(df["date_str"].tolist(), df["distance_miles"].tolist(), "Activity")
    m_raw["hovertemplate"] = "Date: %{x}<br>Miles: %{y:.2f}<extra>%{meta}</extra>"
    
    m_trend = make_trace(grouped["x"].tolist(), grouped["miles_smoothed"].tolist(), "Trend", mode="lines", color="#4DA3FF")
    m_trend["hovertemplate"] = "Date: %{x}<br>Miles: %{y:.2f}<extra>%{meta}</extra>"
    
    # 3. Build Pace Traces
    p_raw = make_trace(df["date_str"].tolist(), df["pace_min_per_mile"].tolist(), "Pace")
    # We add custom text for the pace hover
    p_raw["text"] = [format_pace(p) for p in df["pace_min_per_mile"].tolist()]
    p_raw["hovertemplate"] = "Date: %{x}<br>Pace: %{text}<extra>%{meta}</extra>"

    p_trend = make_trace(grouped["x"].tolist(), grouped["pace_smoothed"].tolist(), "Trend", mode="lines", color="#4DA3FF")
    p_trend["text"] = [format_pace(p) for p in grouped["pace_smoothed"].tolist()]
    p_trend["hovertemplate"] = "Date: %{x}<br>Pace: %{text}<extra>%{meta}</extra>"

    return {
        "mile_chart": build_chart_config([m_trend, m_raw], "Miles"),
        "pace_chart": build_chart_config([p_trend, p_raw], "Pace (min/mi)", reverse_y=True)
    }