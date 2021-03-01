FROM python:3

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

ARG MINION_NUMS

COPY . .

CMD python ./app.py hashes.txt $MINION_NUMS
