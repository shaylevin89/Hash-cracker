import sys
import logging
import config
from prestart import file_valid, range_provider
from minion import Minion
import concurrent.futures

LOG_FORMAT = "%(levelname)s %(asctime)s - %(message)s"
logging.basicConfig(level=config.logging_level, format=LOG_FORMAT)


class Master:
    def __init__(self, minion_amount, hash_set, range_list):
        self.range_list = range_list
        self.minion_amount = minion_amount
        self.hash_set = hash_set
        self.cracked_hashes = dict()
        self.crashed_ranges = []

    def run(self):
        minions = [Minion(
            self.range_list[minion_num], config.url + str(minion_num + 1) + config.port, self.hash_set, minion_num)
                   for minion_num in range(self.minion_amount)]
        with concurrent.futures.ThreadPoolExecutor() as executor:
            minions_futures = {executor.submit(minion.send_hashes, minion.hash_set): minion for minion in minions}
            for minion in concurrent.futures.as_completed(minions_futures):
                res = minion.result()
                if res:  # minion alive
                    if isinstance(res, dict):
                        self.cracked_hashes.update(res)
                    if len(self.hash_set) == len(self.cracked_hashes):  # all the hashes has been cracked
                        logging.info('finish cracking successfully')
                        for hash_key in self.cracked_hashes:
                            logging.info(f'{hash_key}: {self.cracked_hashes[hash_key]}')
                        exit()
                    else:  # if res == 'Ready to work':
                        if len(self.crashed_ranges) != 0:
                            minions_futures[minion].pass_range = self.crashed_ranges[0]
                            print(f'len of uncracked crashed ranges {len(self.crashed_ranges)}')
                            self.crashed_ranges = self.crashed_ranges[1:]
                            minions_futures[minion].send_range()
                        else:  # no more password to work with
                            logging.info('All possible passwords has been checked')
                            if len(self.cracked_hashes) > 0:
                                logging.info('This is the cracked hashes:')
                                for hash_key in self.cracked_hashes:
                                    logging.info(f'{hash_key}: {self.cracked_hashes[hash_key]}')
                                exit()
                            logging.info('No cracked hashes')
                            exit()
                else:
                    self.crashed_ranges.append(minions_futures[minion].pass_range)
                    del minions_futures[minion]


def start():
    logging.info(sys.argv)
    if len(sys.argv) == 3 and sys.argv[2].isdigit() and int(sys.argv[2]) > 0:
        path = sys.argv[1]
        minion_amount = int(sys.argv[2])
        hash_set = file_valid(path)
        logging.info(f'Hash file has {len(hash_set)} valid hashes')
        range_list = range_provider(minion_amount)
        logging.info(f'Range list ready with {len(range_list)} ranges')
        master = Master(minion_amount, hash_set, range_list)
        master.run()
    else:
        logging.error(config.instruction)


if __name__ == '__main__':
    start()
