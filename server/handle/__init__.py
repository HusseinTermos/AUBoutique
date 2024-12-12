from .accounts import *
from .products import *
from .messaging import *

def home():
    return build_http_response(status_code=200,
                                    body=prep_json({"message": "I hear you loud and clear!"}))
