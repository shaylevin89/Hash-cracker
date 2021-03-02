# hash-cracker

Requirements:
- docker
- docker-compose

Design:

Minion-server implements an API that receives tasks from master in order to crack hashes.

Master is responsible for assigning and controlling the minions by making requests to their API. 

Crash Handling:

In case of minion becomming unavailble, the work he was assigned to added to a queue of unresolved tasks.
Minions that completed their assignment are reassinged with task from the queue.

Usage:

./run.sh \<path to hash file> \<minion amount>

Example:

./run.sh hashes.txt.example 4

