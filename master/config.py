import logging
import os

logging_level = os.getenv("LOGGING_LEVEL", logging.INFO)
timeout = 3
crack_timeout = 10
port = ':3489'
mid_name = '127.0.0.'  # 'hash-cracker_minion_'
url = 'http://' + mid_name
instruction = """Please start again:
python3 app.py <path to hash file> <minion amount>
Example- python3 app.py ./hashes.txt 4"""

print(mid_name)