import sys
import logging
import config
from prestart import file_valid, range_provider
from minion import Minion
import concurrent.futures
import threading
import os

LOG_FORMAT = "%(levelname)s %(asctime)s - %(message)s"
logging.basicConfig(level=config.logging_level, format=LOG_FORMAT)


class Master:
    def __init__(self, minion_amount, hash_set, range_list):
        self.range_list = range_list
        self.minion_amount = minion_amount
        self.hash_set = hash_set
        self.cracked_hashes = dict()
        self.crashed_ranges = []
        self.minions = None
        self.checked_ranges = 0

    def run(self):
        self.minions = [Minion(
            self.range_list[minion_num], config.url + str(minion_num + 1) + config.port, self.hash_set, minion_num)
            for minion_num in range(self.minion_amount)]
        with concurrent.futures.ThreadPoolExecutor() as executor:
            minions_futures = {executor.submit(minion.send_hashes, self.hash_set): minion for minion in self.minions}
            self.as_complete(minions_futures)

    def regenerate_range_futures(self, minion, pass_range):
        with concurrent.futures.ThreadPoolExecutor() as executor:
            minions_futures = {executor.submit(minion.send_range, pass_range): minion}
            self.as_complete(minions_futures)

    def as_complete(self, future_dict):
        for minion_future in concurrent.futures.as_completed(future_dict):
            res = minion_future.result()
            self.result_handler(res, future_dict[minion_future])

    def result_handler(self, res, minion):
        if res:  # minion alive
            self.checked_ranges += 1
            if isinstance(res, dict):
                self.cracked_hashes.update(res)
            if len(self.hash_set) == len(self.cracked_hashes):  # all the hashes has been cracked
                logging.info('Finish cracking successfully')
                for hash_key in self.cracked_hashes:
                    logging.info(f'{hash_key}: {self.cracked_hashes[hash_key]}')
                os.kill(os.getpid(), 9)
            else:  # if the work did not finished yet. maybe 'ready' maybe cracked dict
                if len(self.crashed_ranges) != 0:
                    tmp_range = self.crashed_ranges[0]
                    self.crashed_ranges = self.crashed_ranges[1:]
                    t1 = threading.Thread(target=self.regenerate_range_futures, args=[minion, tmp_range])
                    # self.regenerate_range_futures(minion, tmp_range)
                    t1.start()
                elif self.checked_ranges == self.minion_amount:  # no more password to work with
                    logging.info('All possible passwords has been checked')
                    if len(self.cracked_hashes) != 0:  # there is cracked hashes
                        logging.info('This is the cracked hashes:')
                        for hash_key in self.cracked_hashes:
                            logging.info(f'{hash_key}: {self.cracked_hashes[hash_key]}')
                    else:
                        logging.info('No cracked hashes')
        else:  # False is received. minion crashed
            self.crashed_ranges.append(minion.pass_range)


def start():
    logging.info(sys.argv)
    if len(sys.argv) == 3 and sys.argv[2].isdigit() and int(sys.argv[2]) > 0:
        path = sys.argv[1]
        minion_amount = int(sys.argv[2])
        hash_set = file_valid(path)
        logging.info(f'Hash file has {len(hash_set)} valid hashes')
        range_list = range_provider(minion_amount)
        logging.info(f'Range list ready with {len(range_list)} ranges for {minion_amount} minions')
        master = Master(minion_amount, hash_set, range_list)
        master.run()
    else:
        logging.error(config.instruction)


if __name__ == '__main__':
    start()
