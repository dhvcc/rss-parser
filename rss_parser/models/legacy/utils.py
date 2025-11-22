from re import sub


def camel_case(s: str):
    s = sub(r"([_\-])+", " ", s).title().replace(" ", "")
    return "".join([s[0].lower(), s[1:]])


def snake_case(s: str):
    return sub(r"(?<!^)(?=[A-Z])", "_", s).lower()
