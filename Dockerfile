FROM python:3.8
ENV PYTHONUNBUFFERED 1
WORKDIR /usr/src/app
COPY requirements.txt /usr/src/app/
RUN pip install --src /usr/local/src -r requirements.txt
