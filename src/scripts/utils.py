from typing import List
from random import choice, choices, randint
import string

def generate_email(domain:str) -> str:
    # Choose a random length for the email address
    email_length = randint(6, 10)

    # Generate a random email address
    email = "".join(
        choices(string.ascii_lowercase + string.digits, k=email_length)
    )
    email = email + "@" + domain

    return email


def generate_password() -> str:
    # Generate a random password
    length = randint(8, 20)
    password = "".join(
        choices(string.ascii_letters + string.digits + "#()!", k=length)
    )

    return password


# s for single d for double
def generate_line_creds(count: int, creds_type: str = "s", domains:List[str]=["example.com"]) -> List[str]:
    creds: List[str] = []
    for _ in range(count):
        new_string = (
            f"{generate_email(choice(domains))} {generate_password()}"
            if creds_type == "s"
            else f"{generate_email(choice(domains))} {generate_password()} {generate_email(choice(domains))} {generate_password()}"
        )
        creds.append(new_string)
    return creds