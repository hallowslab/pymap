import random
import string
from typing import List


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


INVALID_HOSTS = ["1.1.1.1.1.1", "40000000312", "not_hostname", "", "       ", "\t\n"]

# One user
RANDOM_VALID_CREDS = generate_line_creds(10)

# Two users
RANDOM_VALID_CREDS_2 = generate_line_creds(5, "d")

# One user
RANDOM_VALID_CREDS_3 = [generate_line_creds(3), generate_line_creds(6)]

# two users
RANDOM_VALID_CREDS_4 = [generate_line_creds(2, "d"), generate_line_creds(4, "d")]
