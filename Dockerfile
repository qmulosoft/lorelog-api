FROM python:3.8

RUN mkdir -p /home/lorelog/data
RUN mkdir /home/lorelog/app

RUN pip3 install poetry
COPY poetry.lock pyproject.toml /home/lorelog/app/

RUN cd /home/lorelog/app && poetry config virtualenvs.create false && poetry install -n

RUN pip3 install uwsgi

COPY src /home/lorelog/app/src
COPY wsgi.py /home/lorelog/app
COPY db /home/lorelog/app/db

WORKDIR /home/lorelog/app
EXPOSE 4242

ENV LL_API_DATA /home/lorelog/data
ENV LL_API_MIGRATION_DIR /home/lorelog/app/db/sqlite/migrations

CMD ["uwsgi", "-c", "/home/lorelog/app/src/llwsgi/uwsgi.ini"]
