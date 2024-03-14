# base image
FROM python:3.8.0-alpine

LABEL MAINTAINER="Dhiraj Patra <dpatra@presto.com>"

ENV DEBUG true

ENV GROUP_ID=1000 \
    USER_ID=1000

# set working directory
RUN mkdir -p /var/www
WORKDIR /var/www

# copy entrypoint.sh
COPY ./entrypoint.sh /var/www/entrypoint.sh

COPY ./gunicorn_config.py /var/www/gunicorn_config.py

# add requirements (to leverage Docker cache)
ADD ./requirements.txt /var/www/requirements.txt

# install requirements
RUN pip install -r requirements.txt

# copy project
COPY . /var/www/


# RUN addgroup -g $GROUP_ID www
# RUN adduser -D -u $USER_ID -G www www -s /bin/sh

# USER www

# EXPOSE 5000

ENTRYPOINT ["/var/www/entrypoint.sh"]
