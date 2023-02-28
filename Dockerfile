FROM python

COPY . /
WORKDIR /

RUN pip install pyTelegramBotAPI
RUN pip install psycopg2
RUN pip install redis


CMD ["python", "./bot.py"]
