import os


def get_env(key, required=False, or_else=None):
    value = os.environ.get(key)

    if required and or_else:
        print(
            f"get_env(): for {key}, or_else parameter was ignored because this variable is required")

    if value is not None:
        return value
    else:
        if required:
            raise RuntimeError(
                f"Required environment variable {key} is missing.")
        else:
            return or_else


# MongoDB connection string
MONGO_CONNECTION_STRING = get_env("MONGO_CONNECTION_STRING", required=True)
# DB name
MONGO_DB = get_env("MONGO_DB", or_else='quotes')
