import logging
import config
import requests
import json

LOG_FORMAT = "%(levelname)s %(asctime)s - %(message)s"
logging.basicConfig(level=config.logging_level, format=LOG_FORMAT)


class MinionController:
    def __init__(self, pass_range, address, hash_set, minion_id):
        self.minion_id = minion_id+1
        self.pass_range = pass_range
        self.address = address
        self.hash_set = hash_set
        self.received_hash = dict()

    def send_hashes(self, hash_set=None, timeout=config.timeout):
        """Chaining of send hashes, send password range and send 'start crack' command together.
        send health check if cracking request reached time out.
        return response from minion.
        return False if error occurred"""
        if not hash_set:
            hash_set = self.hash_set
        hash_accepted = 0
        if timeout > 30:
            return False
        try:
            res = requests.post(self.address + '/hashes', str(hash_set).encode(), timeout=timeout)
            if res.status_code == 200:
                return self.send_range()
        except requests.ConnectionError:
            logging.error(f'minion {self.minion_id} not reachable - crashed')
            return False
        except requests.ReadTimeout:
            logging.error(f'the {hash_accepted}th request reached timeout in minion {self.minion_id}')
            return self.send_hashes(hash_set, timeout+10)
        except Exception as e:
            logging.error(e)
            return False

    def send_range(self, pass_range=None, timeout=config.timeout):
        if not pass_range:
            pass_range = self.pass_range
        self.pass_range = pass_range
        if timeout > 30:
            return False
        try:
            res = requests.post(self.address + '/range', str(pass_range), timeout=timeout)
            if res.status_code == 204:
                logging.info(f'range: {pass_range} has been sent to minion {self.minion_id}')
                return self.start_crack()
            return False
        except requests.ConnectionError:
            logging.error(f'minion {self.minion_id} not reachable - connection error')
            return False
        except requests.ReadTimeout:
            logging.error(f'range post request reached timeout')
            return self.send_range(timeout=timeout+10)

    def start_crack(self):
        try:
            res = requests.get(
                self.address + '/cracked_hashes/' + str(len(self.hash_set)), timeout=config.crack_timeout)
            if res.status_code == 400:
                logging.error(f'the minion did not get full hash set or the range')
                return False
            elif res.status_code == 200:
                return self.crack_succeed(res)
        except requests.ConnectionError:
            logging.error(f'minion {self.minion_id} not reachable - connection error')
            return False
        except requests.ReadTimeout:
            return self.health_check()
        except Exception as e:
            logging.error(e)
            return False

    def health_check(self, timeout=config.crack_timeout + 10):
        timeout = timeout
        try:
            res = requests.get(self.address + '/health_check', timeout=timeout)
            if res.status_code == 200:
                return self.crack_succeed(res)
            return False
        except requests.ConnectionError:
            logging.error(f'minion {self.minion_id} not reachable - connection error')
            return False
        except requests.ReadTimeout:
            return self.health_check(timeout + 10)
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
            logging.info(f'minion {self.minion_id} finish range {self.pass_range} without cracking')
            return 'Ready to work'

    def delete_minion(self):
        try:
            requests.delete(self.address + '/kill_minion', timeout=config.timeout)
        except requests.ConnectionError:
            logging.error(f'minion {self.minion_id} not reachable - connection error')
            return False
        except Exception as e:
            logging.error(e)
