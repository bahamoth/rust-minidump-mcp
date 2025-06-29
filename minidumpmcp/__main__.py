"""Allow execution as python -m minidumpmcp or via uvx."""

if __name__ == "__main__":
    from minidumpmcp.cli import app

    app()
