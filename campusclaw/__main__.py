"""Development-server entry point for ``python -m campusclaw``."""

from campusclaw import create_app

app = create_app()


if __name__ == "__main__":
    app.run()
