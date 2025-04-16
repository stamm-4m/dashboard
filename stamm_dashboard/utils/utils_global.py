import plotly.graph_objects as go

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
                plot_bgcolor="lightgray",  # Fondo gris para efecto "deshabilitado"
                paper_bgcolor="lightgray",
            ),
        } 