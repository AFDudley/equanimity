#!/usr/bin/env python

from server import create_app
from config.dev import SERVER_ADDRESS, SERVER_PORT

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host=SERVER_ADDRESS, port=SERVER_PORT)
