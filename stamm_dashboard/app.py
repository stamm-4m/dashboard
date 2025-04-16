import logging
import flask
import dash_bootstrap_components as dbc  # type: ignore
import argparse
from dash import Dash
from stamm_dashboard.layouts.main_layout import layout

# Set up logging configuration
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),  # Print to console
        logging.FileHandler('app.log')  # Log to a file
    ]
)

logging.info("Starting stamm dashboard")

def parser() -> argparse.Namespace:
    """
    Parse command line arguments for the dashboard.
    """
    parser = argparse.ArgumentParser(description="Start the dashboard.")
    parser.add_argument(
        "-c", "--config", type=str, default="config.yaml", help="Path to the configuration file"
    )
    parser.add_argument("-port", "--port", type=int, default=8050, help="Port to run the server on")

    parser.add_argument("-d", "--debug", action="store_true", help="Enable debug mode")
    parser.add_argument("-ml", "--mlrepository", type=str, default="/Users/koeho006/git/stamm/ml-repository", help="Path to the ML repository")

    # Parse the arguments
    args = parser.parse_args()
    return args

def main():
    args = parser()

    logging.info("Arguments: %s", args)

    # Crear el servidor Flask
    server = flask.Flask(__name__)

    # Crear la aplicación Dash y conectar con Flask
    app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP], server=server, suppress_callback_exceptions=True)

    app.layout = layout()

    app.run(debug=args.debug, host="0.0.0.0", port=args.port)

if __name__ == "__main__":
    main()
