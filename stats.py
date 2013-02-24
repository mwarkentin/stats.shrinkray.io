import os

from flask import Flask

app = Flask(__name__)


def bool_env(val):
    """Replaces string based environment values with Python booleans"""
    return True if os.environ.get(val, False) == 'True' else False

if __name__ == '__main__':
    app.debug = bool_env('DEBUG')
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
