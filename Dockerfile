FROM python:latest

LABEL maintainer="ndlexecme@gmail.com"

COPY requirements.txt /requirements.txt
RUN pip install -r requirements.txt

COPY . /app
WORKDIR /app

ENTRYPOINT ["python", "ptp-bot.py"]
