"""Application entry point."""
from app import create_app

application = create_app()
app = application  # Alias for gunicorn compatibility

if __name__ == "__main__":
    application.run(host="0.0.0.0", port=5000, debug=True)
