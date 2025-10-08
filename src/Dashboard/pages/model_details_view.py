import dash.html as html
import dash_bootstrap_components as dbc

def generate_output_items(predictions):
    """Generate a styled list of output items with a badge and all available fields."""
    if not predictions:
        return html.P("No output information available.")

    items = []
    for pred in predictions:
        # Extraer nombre (Badge) y el resto de los campos
        name = pred.get("name", "Unnamed Output")

        # Contenedor para los demás campos
        details = []
        for key, value in pred.items():
            if key == "name":
                continue  # el badge se muestra arriba
            if isinstance(value, dict):
                subitems = [f"{subkey}: {subval}" for subkey, subval in value.items()]
                value_str = ", ".join(subitems)
            else:
                value_str = str(value)

            details.append(
                html.Div([
                    html.Span(f"{key}: ", className="fw-bold text-secondary"),
                    html.Span(value_str)
                ], className="ms-2")
            )

        # Cada predicción se muestra en un ListGroupItem con Badge + detalles
        items.append(
            dbc.ListGroupItem(
                html.Div([
                    dbc.Badge(name, color="success", className="me-2 mb-1"),
                    html.Div(details, className="mt-1")
                ])
            )
        )

    return dbc.ListGroup(items, flush=True)

def generate_model_details_view(config):
    if not config:
        return html.P("The configuration for the selected model was not found.", style={'textAlign': 'center'})

    model_ident = config['model_identification']
    model_desc = config['model_description']
    model_pack = model_desc.get('packages', [])
    model_train = config['training_information']
    features = config['inputs'].get('features', 'N/A')
    predictions = config.get("outputs", {}).get("information", [])

    name = model_ident.get('name', 'N/A')
    version = model_ident.get('version', 'N/A')
    uuid = model_ident.get('UUID', 'N/A')
    author = model_ident.get('author', 'N/A')
    doi = model_ident.get('doi', 'N/A')
    creation_date = model_ident.get('creation_date', 'N/A')

    model_name = model_desc.get('model_name', 'N/A')
    learner = model_desc.get('learner', 'N/A')
    model_file = model_desc.get('config_files', {}).get('model_file', 'N/A')
    model_type = model_desc.get('model_type', 'N/A')
    description = model_desc.get('description', 'N/A')
    language = model_desc.get('language', 'N/A')

    hyperparameters = model_train.get('hyperparameters', {})

    return (
        dbc.Accordion(
            [
                dbc.AccordionItem(
                    title=html.Div(f"Model name: {model_name}"),
                    children=[
                        dbc.Row([
                            dbc.Col(html.Div([
                                html.H4("Identification"),
                                html.P(f"Name: {name}"),
                                html.P(f"Version: {version}"),
                                html.P(f"UUID: {uuid}"),
                                html.P(f"Author: {author}"),
                                html.P(f"DOI: {doi}"),
                                html.P(f"Creation date: {creation_date}"),
                            ]), width=6),
                            dbc.Col(html.Div([
                                html.H4("Description"),
                                html.P(f"Learner: {learner}"),
                                html.P(f"File: {model_file}"),
                                html.P(f"Type: {model_type}"),
                                html.P(f"Language: {language}"),
                                html.P(f"Description: {description}"),
                            ]), width=6),
                        ], className="mb-4"),
                        dbc.Row([
                            dbc.Col(html.Div([
                                html.H4("Hyperparameters"),
                                dbc.ListGroup([
                                    dbc.ListGroupItem(f"Number of trees: {hyperparameters.get('number_of_trees', 'N/A')}"),
                                    dbc.ListGroupItem(f"Max tree depth: {hyperparameters.get('max_tree_depth', 'N/A')}"),
                                    dbc.ListGroupItem(f"Min instances per leaf: {hyperparameters.get('min_number_instances_per_leaf', 'N/A')}"),
                                    dbc.ListGroupItem(f"Committees: {hyperparameters.get('committees', 'N/A')}"),
                                    dbc.ListGroupItem(f"Instance based corrections: {hyperparameters.get('instance_based_corrections', 'N/A')}"),
                                ], flush=True),
                            ]), width=6),
                            dbc.Col(html.Div([
                                html.H4("Training Information"),
                                dbc.ListGroup([
                                    dbc.ListGroupItem(f"Number of instances: {model_train.get('number_of_instances', 'N/A')}"),
                                    dbc.ListGroupItem(f"Max tree depth: {model_train['hyperparameters'].get('max_tree_depth', 'N/A')}"),
                                    dbc.ListGroupItem(f"Validation: {model_train.get('validation', 'N/A')}"),
                                    dbc.ListGroupItem(f"Experiments ID: {', '.join(map(str, model_train.get('experiments_ID', [])))}"),
                                ], flush=True),
                            ]), width=6),
                        ], className="mb-4"),
                        dbc.Row([
                            dbc.Col(html.Div([
                                html.H4("Packages"),
                                dbc.ListGroup([
                                    dbc.ListGroupItem([
                                        html.Strong(f"{package.get('package', 'Unknown')}, Version: {package.get('version', 'Unknown')}"),
                                        html.Ul([
                                            html.Li(class_name) for class_name in package.get('classes', [])
                                        ]) if 'classes' in package else html.P("No classes available")
                                    ]) for package in model_pack if isinstance(package, dict)
                                ] if isinstance(model_pack, list) else [dbc.ListGroupItem("No packages available")], flush=True),
                            ]), width=12),
                        ]),
                        dbc.Row([
                            dbc.Col(html.Div([
                                html.H4("Inputs"),
                                dbc.ListGroup([
                                    dbc.ListGroupItem(html.Span([
                                        dbc.Badge(feature["name"], color="primary", className="me-2"),
                                        f"{feature['description']} ({feature['units']})",
                                    ])) for feature in features
                                ], flush=True),
                            ]), width=12),
                        ]),
                        dbc.Row([
                            dbc.Col(html.Div([
                                html.H4("Outputs"),
                                generate_output_items(predictions)
                            ]), width=12),
                        ]),
                    ],
                    className="mb-3",
                )
            ],
            start_collapsed=True,
            flush=False,
        )
    )
