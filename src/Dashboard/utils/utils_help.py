from dash import html
import dash_bootstrap_components as dbc


def make_section(title, data):
    """Helper para mostrar listas de campos y descripciones."""
    if not data:
        return html.I("No information available.")
    return html.Ul([
        html.Li([html.B(f"{key}: "), val.get("description", "")])
        for key, val in data.items()
    ])

def build_models_help(model_info):
    """Muestra información general de un modelo o dataset."""
    return html.Div(
        [
            html.P(model_info["description"], className="text-muted mb-3"),
            dbc.Row([
                dbc.Col([
                    html.H6("Project Information", className="text-primary mt-3"),
                    html.Ul([
                        html.Li(html.B(f"Project ID: {model_info['project_ID']}")),
                        html.Li(html.B(f"Name: {model_info['project_name']}")),
                        html.Li(html.B(f"Coordinator: {model_info['coordinator']}")),
                        html.Li(html.B(f"Start Date: {model_info['start_date']}")),
                        html.Li(html.B(f"End Date: {model_info['end_date']}")),
                    ]),
                ], md=6),
                dbc.Col([
                    html.H6("Database Configuration", className="text-primary mt-3"),
                    make_list_section(model_info.get("db_config")),
                ], md=6),
            ]),
            html.H6("References", className="text-primary mt-4"),
            make_references_section(model_info.get("references")),
        ]
    )

def make_references_section(ref_list):
    """Renderiza referencias bibliográficas."""
    if not ref_list:
        return html.I("No references available.")
    items = []
    for ref in ref_list:
        items.append(
            html.Li([
                html.B(f"{ref['id']} ({ref['year']}): "),
                html.Span(ref['title']),
                html.Br(),
                html.Small(ref.get('apa', ""), className="text-muted"),
            ], className="mb-2")
        )
    return html.Ul(items)

def make_list_section(data_dict):
    """Renderiza listas tipo diccionario."""
    if not data_dict:
        return html.I("No information available.")
    return html.Ul([
        html.Li([html.B(f"{key}: "), str(value)]) for key, value in data_dict.items()
    ])

def build_drift_detector_help(detectors):
    """Crea un accordion con la información de detectores."""
    accordion_items = []
    for path, meta in detectors.items():
        accordion_items.append(
            dbc.AccordionItem(
                title=f"{meta['name']} ({meta['type']})",
                children=[
                    html.P(meta.get("description", ""), className="text-muted mb-3"),
                    html.H6("Inputs", className="mt-3 text-primary"),
                    make_section("Inputs", meta.get("inputs")),
                    html.H6("Parameters", className="mt-3 text-primary"),
                    make_section("Parameters", meta.get("parameters")),
                    html.H6("Output", className="mt-3 text-primary"),
                    html.P(meta["output"]["description"]),
                    make_section("Fields", meta["output"].get("fields", {})),
                ]
            )
        )
    return dbc.Accordion(accordion_items, start_collapsed=True, always_open=False, flush=True)

def build_navigation(sections):
    """Creates a clickable index that scrolls to each section."""
    links = [
        html.Li(
            html.A(
                [
                    html.I(className="bi bi-chevron-right me-2 text-secondary"),
                    section,
                ],
                href=f"#{section.lower().replace(' ', '-')}",
                className="text-decoration-none text-primary fw-semibold"
            ),
            className="mb-2"
        )
        for section in sections
    ]

    return html.Div(
        [
            html.H5(
                [
                    html.I(className="bi bi-journal-text me-2 text-info"),
                    "Sections",
                ],
                className="mb-3 text-secondary"
            ),
            html.Ul(links, className="list-unstyled ps-2"),
            html.Hr(className="mb-4")
        ]
    )

