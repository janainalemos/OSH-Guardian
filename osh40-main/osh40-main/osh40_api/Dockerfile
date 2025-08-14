FROM python:3.8

WORKDIR /api

COPY ./api/*.py /api/

COPY ./.env /api/

COPY ./api/app /api/

RUN pip install --no-cache-dir --upgrade -r /api/requirements.txt
