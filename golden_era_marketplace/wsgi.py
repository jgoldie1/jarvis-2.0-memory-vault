from .dashboard_backend import app


def create_app():
    return app


if __name__ == '__main__':
    app.run()
