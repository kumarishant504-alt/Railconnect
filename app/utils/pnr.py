import random
import string
from datetime import datetime, timezone


def generate_pnr() -> str:
    """Generate a unique PNR: RC + YYMMDD + 6 random alphanumeric chars."""
    date_part = datetime.now(timezone.utc).strftime("%y%m%d")
    random_part = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return f"RC{date_part}{random_part}"
