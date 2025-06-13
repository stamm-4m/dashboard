import dash
from dash import Input, Output, State, dcc, html
import dash_bootstrap_components as dbc
import random
import os


def about_us_layout():
        team_members = get_team_data()
        return html.Div(
            style={
                "backgroundColor": "#f8f9fa",
                "padding": "20px 10px",
                "minHeight": "100vh",
            },
            children=[
                html.Div(
                    children=[
                        html.H1("About us", className="text-center mb-5", style={"color": "#343a40"}),
                        html.P(
                            "We create a prototype to test the performance of your model. Our focus is on providing a reliable and efficient solution to help you evaluate and improve your idea.",
                            className="text-center mb-4",
                            style={"color": "#6c757d", "maxWidth": "800px", "margin": "0 auto"},
                        ),
                    ],
                    className="mb-5",
                ),
                dbc.Container(
                    dbc.Row(
                        [
                            dbc.Col(
                                dbc.Card(
                                    dbc.CardBody([
                                        html.Img(
                                            src=member["image"],
                                            alt=member["name"],
                                            className="img-fluid rounded-circle mb-3 shadow-sm",
                                            style={"width": "120px", "height": "120px", "objectFit": "cover"},
                                        ),
                                        html.H4(member["name"], className="card-title mb-2", style={"color": "#343a40"}),
                                        html.P(member["position"], className="mb-1", style={"color": "#6c757d"}),
                                        html.P(member["institution"], className="mb-3", style={"color": "#6c757d"}),
                                        dbc.ButtonGroup(
                                            [
                                                dbc.Button("LinkedIn", href=member["linkedin"], color="primary", target="_blank", className="me-2"),
                                                dbc.Button("Google Scholar", href=member["scholar"], color="secondary", target="_blank"),
                                            ],
                                            size="sm",
                                        ),
                                    ]),
                                    className="h-100 text-center shadow",
                                    style={"borderRadius": "15px", "border": "none", "padding": "15px"},
                                ),
                                width=4,
                                className="mb-4",
                            )
                            for member in team_members
                        ]
                    ),
                    fluid=True,
                ),
                html.Div(
                    html.P(
                        "© 2024 STAMM Project. All rights reserved.",
                        className="text-center",
                        style={"color": "#6c757d", "marginTop": "50px"},
                    )
                ),
            ],
        )
    
   
def get_team_data():
        assets_directory = "assets/"  # Path where images are stored
        default_image = "https://via.placeholder.com/150"  # Set your default profile image

        members = [
            {
                "name": "David Camilo Corrales", "image": "Camilo.jpeg",
                "position": "Artificial Intelligence R&D",
                "institution": "INRAE",
                "image": "Camilo.jpeg",
                "linkedin": "https://www.linkedin.com/in/david-camilo-corrales-95b2371a6/",
                "scholar": "https://scholar.google.fr/citations?user=WWkHwXwAAAAJ&hl=en",
            },
            {
                "name": "Carlos Suarez", "image": "Carlos.png",
                "position": "FullStack Engineer – R&D",
                "institution": "Department of Telematics, University of Cauca",
                "image": "Carlos.png",
                "linkedin": "https://www.linkedin.com/in/carlos-alberto-suarez-mu%C3%B1oz-7937bb138/",
                "scholar": "https://www.linkedin.com/in/carlos-alberto-suarez-mu%C3%B1oz-7937bb138/",
            },
            {
                "name": "Alexander Astudillo", "image": "Alexander.jpeg",
                "position": "Artificial Intelligence R&D",
                "institution": "INRAE",
                "image": "Alexander.jpeg",
                "linkedin": "https://www.linkedin.com/in/astudillo-lagos-jairo-alexander-2ab524352",
                "scholar": "https://www.linkedin.com/in/astudillo-lagos-jairo-alexander-2ab524352",
            },
            {
                "name": "Juan Valencia", "image": "Juan.jpeg",
                "position": "FullStack Engineer – R&D",
                "institution": "Department of Telematics, University of Cauca",
                "image": "Juan.jpeg",
                "linkedin": "https://www.linkedin.com/in/juanvalencia10/",
                "scholar": "https://www.linkedin.com/in/juanvalencia10/",
            },
            {
                "name": "Esteban Castillo", "image": "Esteban.jpeg",
                "position": "NLP & Data Science Researcher",
                "institution": "Monterrey Institute of Technology (Tec de Monterrey)",
                "image": "Esteban.jpeg",
                "linkedin": "https://www.linkedin.com/in/esteban-castillo-b24940187/",
                "scholar": "https://scholar.google.com.mx/citations?user=JfZpVO8AAAAJ&hl=es",
            },
            {
                "name": "Brett Metcalfe", "image": "Brett.jpeg",
                "position": "Random Micropalaeontologist",
                "institution": "Wageningen University and Visiting Fellow, VU University Amsterdam (NL)",
                "image": "Brett.jpeg",
                "linkedin": "https://www.linkedin.com/in/brett-metcalfe-a2b95738/",
                "scholar": "https://scholar.google.nl/citations?user=EHK0320AAAAJ&hl=en",
            },
            {
                "name": "Jasper Koehorst", "image": "Jasper.jpeg",
                "position": "Bioinformatics Research Scientist – Microbial Communities & Genome Analysis",
                "institution": "Wageningen University & Research",
                "image": "Jasper.jpeg",
                "linkedin": "https://www.linkedin.com/in/jasperkoehorst/",
                "scholar": "https://scholar.google.nl/citations?user=KAfqpDAAAAAJ&hl=nl",
            },
        ]

        # Check if each image exists, else use the default image
        for member in members:
            image_path = os.path.join(assets_directory, member["image"])
            if os.path.exists(image_path):
                member["image"] = f"/assets/{member['image']}"
            else:
                member["image"] = default_image  # Use the default profile image if not found

        return members