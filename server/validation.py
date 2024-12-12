import regex as re
import string
"""Functions that validate the structure of user info"""
def validate_name(s):
    return re.match(r"^[a-zA-Z]+( |\-)[a-zA-Z]+(( |\-)[a-zA-Z]+)?$", s) is not None
def validate_email(s):
    if '@' not in s: return None
    username, rest = s.split('@')
    if '.' not in rest: return None
    return True
def validate_username(s):
    return re.match(r"^([a-zA-z0-9/\-_$])+$", s) is not None

def validate_password(s):
    if len(s) < 8: return None
    if all([l not in s for l in string.ascii_uppercase]):
        return None
    if all([l not in s for l in string.ascii_lowercase]):
        return None
    for l in string.ascii_uppercase + string.ascii_lowercase:
        s = s.replace(l, '')
    if s is None: return None

    return True

    