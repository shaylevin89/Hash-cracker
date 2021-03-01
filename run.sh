#! /bin/bash

usage="2 args required \n./run.sh <path to hash file> <minion amount> \nExample: ./run.sh ./hashes.txt 3"
trap 'echo -e $usage && exit' ERR

if [[ $# -ne 2 || ! "$2" =~ ^[0-9]+$ || $2 -lt 1 ]];
then echo -e $usage && exit;
fi

if ! grep -qe "^[a-f0-9]\{32\}$" $1;
then echo -e "There is no valid hash in the hash file\nPlease provide one and start again" && exit;
fi

cp $1 ./master/hashes.txt
echo MINION_NUMS=$2 > .env

docker-compose build -q
docker-compose up -d --scale minion=$2
docker-compose logs --follow master
docker-compose down
