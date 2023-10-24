from re import sub


def camel_case(s: str):
    return sub(r'(?<!^)(?=[A-Z])', '_', s).lower()
