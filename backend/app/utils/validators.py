import re

IBAN_REGEX = re.compile(r"^[A-Z]{2}[0-9]{2}[A-Z0-9]{11,30}$")


def is_valid_iban(value: str) -> bool:
    normalized = value.replace(" ", "").upper()
    if not IBAN_REGEX.match(normalized):
        return False

    rearranged = normalized[4:] + normalized[:4]
    numeric = "".join(str(ord(char) - 55) if char.isalpha() else char for char in rearranged)
    return int(numeric) % 97 == 1
