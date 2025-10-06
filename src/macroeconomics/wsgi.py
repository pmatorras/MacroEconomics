from dotenv import load_dotenv
load_dotenv()

from .dash_app import create_app

# Create Dash app
app = create_app()
# Expose Flask server for Gunicorn
server = app.server