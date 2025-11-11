import dash.html as html

def format_variable_name(variable_name):
    """
    Convert a variable name from snake_case to title case with spaces.

    Example:
        'computed_variable' -> 'Computed Variable'
        'sensor' -> 'Sensor'
        'soft_sensor' -> 'Soft Sensor'

    Parameters:
        variable_name (str): Variable name in snake_case format.

    Returns:
        str: Formatted variable name in title case with spaces.
    """
    return ' '.join(word.capitalize() for word in variable_name.split('_'))


def generate_projects_details_view(data):
    if not data:
        return html.P("The information projects was not found.", style={'textAlign': 'center'})

    description = data.get('description', [])
    
    return (
        html.Div(
            description,
            style={
                "height": "300px",  # Altura fija del contenedor
                "overflowY": "scroll",  # Scroll vertical
                "border": "1px solid #ccc",
                "padding": "10px",
                "backgroundColor": "#f8f9fa"
            }
        )
    )
