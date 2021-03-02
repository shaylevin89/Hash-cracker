from flask import Flask, request
from hashlib import md5
from time import sleep
import logging
import os

logging_level = os.getenv("LOGGING_LEVEL", logging.INFO)
LOG_FORMAT = "%(levelname)s %(asctime)s - %(message)s"
logging.basicConfig(level=logging_level, format=LOG_FORMAT)
hash_set = set()
password_range = [0, 0]
success = dict()
start_cracking = False
cracking_ended = False
app = Flask(__name__)


def hash_cracker(hash_set, password_range):
    logging.info('start cracking')
    global start_cracking, cracking_ended
    start_cracking = True
    cracking_ended = False
    for password in range(password_range[0], password_range[1]):
        password = '0' + str(password)
        password_hash = md5(password.encode()).hexdigest()
        if password_hash in hash_set:
            success[password_hash] = password
        if len(hash_set) == len(success):
            break
    cracking_ended = True
    logging.info(f'finish cracking {start_cracking}, {cracking_ended}')


@app.route("/hashes", methods=['POST'])
def hashes_builder():
    data = request.data.decode()
    data = data[1:-1].split(", ")
    for hash_val in data:
        hash_set.add(hash_val[1:-1])
    return "", 200


@app.route("/range", methods=['POST'])
def range_builder():
    global success, start_cracking, cracking_ended
    success = dict()
    start_cracking = False
    cracking_ended = False
    data = request.data.decode()
    password_range[0] = int(data[1:10])
    password_range[1] = int(data[12:-1])
    return '', 204


@app.route("/cracked_hashes/<hashes_amount>", methods=['GET'])
def cracked_hashes(hashes_amount=None):
    if len(hash_set) == int(hashes_amount) and password_range[1] != 0:
        hash_cracker(hash_set, password_range)
        return success
    return 'not ready', 400


@app.route("/health_check", methods=['GET'])
def health_check():
    global start_cracking, cracking_ended
    if start_cracking:
        if not cracking_ended:
            while not cracking_ended:
                sleep(1)
            return success
        return success
    return 'something went wrong', 404


@app.route("/kill_minion", methods=['DELETE'])
def kill_minion():
    res = request.environ.get('werkzeug.server.shutdown')
    if not res:
        logging.error('not werkzeug')
    else:
        res()
    return ''


if __name__ == '__main__':
    app.run('0.0.0.0', 3489)
