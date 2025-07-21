import uuid
import random
import string
from datetime import datetime
import time

def generate_payment_reference(prefix="PAY", suffix_length=6, log_file="payment_references.txt"):
    """
    Generate a unique payment reference and save it to a file.

    Args:
        prefix (str): Optional prefix for the reference.
        suffix_length (int): Length of the random suffix.
        log_file (str): File where references are stored.

    Returns:
        str: Unique payment reference.
    """
    timestamp = int(time.time())
    readable_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    random_suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=suffix_length))
    reference = f'{prefix}{timestamp}{random_suffix}'

    log_entry = f"[{readable_timestamp}] {reference}\n"

    try:
        with open (log_file, 'a') as f:
            f.write(log_entry + '\n')
    except IOError as e:
         print(f"❌ Failed to write to log file: {e}")

    return reference