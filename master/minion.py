import logging
import config
import requests
import json

LOG_FORMAT = "%(levelname)s %(asctime)s - %(message)s"
logging.basicConfig(level=config.logging_level, format=LOG_FORMAT)


class Minion:
    def __init__(self, pass_range, address, hash_set, minion_id):
        self.minion_id = minion_id+1
        self.pass_range = pass_range
        self.address = address
        self.hash_set = hash_set
        self.received_hash = dict()

    def send_hashes(self, hash_set=None):
        if not hash_set:
            hash_set = self.hash_set
        hash_accepted = 0
        try:
            for hash_val in hash_set:
                res = requests.post(self.address + '/hashes', hash_val.encode(), timeout=config.timeout)
                if res.text == 'data':
                    hash_accepted += 1
            if hash_accepted == len(hash_set):
                logging.debug(f'all {hash_accepted} hashes has been sent')
                return self.send_range()
        except requests.ConnectionError:
            logging.error(f'minion {self.minion_id} not reachable - crashed')
            return False
        except requests.ReadTimeout:
            logging.error(f'the {hash_accepted}th request reached timeout in minion {self.minion_id}')
            self.send_hashes(hash_set)
        except Exception as e:
            logging.error(e)
            return False

    def send_range(self, pass_range=None):
        if not pass_range:
            pass_range = self.pass_range
        self.pass_range = pass_range
        try:
            requests.post(self.address + '/range', str(pass_range), timeout=config.timeout)
            logging.info(f'range: {pass_range} has been sent to minion {self.minion_id}')
            return self.send_start_crack()
        except requests.ConnectionError:
            logging.error(f'minion {self.minion_id} not reachable - crashed')
            return False
        except requests.ReadTimeout:
            logging.error(f'range post request reached timeout')
            self.send_range()

    def send_start_crack(self):
        try:
            res = requests.get(
                self.address + '/cracked_hashes/' + str(len(self.hash_set)), timeout=config.crack_timeout)
            if res.text == 'not ready':
                logging.error(f'the minion did not get full hash set or the range')
                # TODO restart?
            elif res.status_code == 200:
                return self.crack_succeed(res)
        except requests.ConnectionError:
            logging.error(f'minion {self.minion_id} not reachable - crashed')
            return False
        except requests.ReadTimeout:
            return self.health_check_rec()
        except Exception as e:
            logging.error(e)
            return False

    def health_check_rec(self, timeout=config.crack_timeout + 10):
        timeout = timeout
        try:
            res = requests.get(self.address + '/health_check', timeout=timeout)
            if res.status_code == 200:
                return self.crack_succeed(res)
            return res.text
        except requests.ConnectionError:
            logging.error(f'minion {self.minion_id} not reachable - crashed')
            return False
        except requests.ReadTimeout:
            return self.health_check_rec(timeout + 10)
        except Exception as e:
            logging.error(e)
            return False

    def crack_succeed(self, res):
        rec_json = res.text
        self.received_hash = json.loads(rec_json)
        if len(self.received_hash) != 0:  # minion cracked some hashes
            logging.info(f'minion {self.minion_id} cracked this hashes:')
            for hash_key in self.received_hash:
                logging.info(f'{hash_key}: {self.received_hash[hash_key]}')
            return self.received_hash
        else:  # minion finished the range without cracking
            logging.info(f'minion {self.minion_id} finished without cracking')
            return 'Ready to work'

    def delete_minion(self):
        try:
            requests.delete(self.address + '/kill_minion', timeout=config.timeout)
        except requests.ConnectionError:
            logging.error(f'minion {self.minion_id} not reachable - crashed')
            return False
        except Exception as e:
            logging.error(e)
