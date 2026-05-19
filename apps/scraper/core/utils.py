import re

def safe_name(s):
    safe_s = re.sub(r'[^\w\-_\. ]', '_', s)
    return safe_s