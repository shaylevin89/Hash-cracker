import re
import config


def md5_valid(string_to_check):
    if re.fullmatch('[a-f0-9]{32}', string_to_check):
        return True
    return False


def file_valid(path):
    try:
        hash_set = set()
        f = open(path, 'r')
        for line in f:
            if line[-1] == '\n':
                line = line[:-1]
            if md5_valid(line):
                hash_set.add(line)
        return hash_set
    except Exception as e:
        print(e)
        print(config.instruction)
        exit()


def range_provider(minions_num):  # -> list[(start, end)]
    total_pos = 100000000
    range_len = total_pos // minions_num
    range_list = []
    start = 500000000
    for minion in range(1, minions_num + 1):
        if minion == minions_num:
            range_list.append((start, 600000000))
            return range_list
        range_list.append((start, start + range_len))
        start += range_len
