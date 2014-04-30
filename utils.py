import os


def bool_env(val):
    """
    Replaces string based environment values with Python booleans

    """

    return True if os.environ.get(val, False) == 'True' else False
