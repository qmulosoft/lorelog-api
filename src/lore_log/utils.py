import uuid


def generate_new_id():
    return str(uuid.uuid4()).replace("-", "")


# TODO this is really not secure against any real effort. But, for very short term its easier
JWT_KEY = generate_new_id()
