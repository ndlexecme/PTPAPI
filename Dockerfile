from python:latest

COPY requirements.txt /requirements.txt
RUN pip install -r requirements.txt

COPY . /app
WORKDIR /app

ENV PTP_APIUSER
ENV PTP_APIKEY
ENV PTP_DISCORD_TOKEN

CMD ["python", "ptp-bot.py"]
