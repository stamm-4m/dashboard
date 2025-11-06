import plotly.graph_objects as go
import re

disabled_figure = {
            "data": [],
            "layout": go.Layout(
                xaxis={"title": "X Axis", "visible": False},
                yaxis={"title": "Y Axis", "visible": False},
                annotations=[
                    {
                        "text": "Graph Disabled",
                        "xref": "paper",
                        "yref": "paper",
                        "showarrow": False,
                        "font": {"size": 20, "color": "gray"},
                    }
                ],
                plot_bgcolor="lightgray",  # background gray to effect "disabilabled"
                paper_bgcolor="lightgray",
            ),
        } 

