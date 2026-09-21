import re

IBAN_REGEX = re.compile(r"^[A-Z]{2}[0-9]{2}[A-Z0-9]{11,30}$")


def is_valid_iban(value: str) -> bool:
    return bool(IBAN_REGEX.match(value.replace(" ", "").upper()))
