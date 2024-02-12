from typing import List
import random
import string

def generate_email() -> str:
    # Choose a random length for the email address
    email_length = random.randint(6, 10)

    # Generate a random email address
    email = "".join(
        random.choices(string.ascii_lowercase + string.digits, k=email_length)
    )
    email = email + "@example.com"

    return email


def generate_password() -> str:
    # Generate a random password
    length = random.randint(8, 20)
    password = "".join(
        random.choices(string.ascii_letters + string.digits + "#()!", k=length)
    )

    return password


# s for single d for double
def generate_line_creds(count: int, creds_type: str = "s") -> List[str]:
    creds: List[str] = []
    for _ in range(count):
        new_string = (
            f"{generate_email()} {generate_password()}"
            if creds_type == "s"
            else f"{generate_email()} {generate_password()} {generate_email()} {generate_password()}"
        )
        creds.append(new_string)
    return creds