FROM python:latest

LABEL maintainer="ndlexecme@gmail.com"

COPY requirements.txt /requirements.txt
RUN pip install -r requirements.txt

COPY . /app
WORKDIR /app

CMD ["python", "ptp-bot.py"]
