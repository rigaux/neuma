
FROM python:3.10-alpine

ADD requirements.txt tmp/requirements.txt

RUN apk update && apk add swig

    
RUN apk update && \
  # Neuma dependencies requirements
  apk add --virtual build gcc musl-dev && \
  apk add --virtual build g++ musl-dev && \
  # PostgreSQL
  apk add postgresql-dev && \
  # Install Neuma Python dependencies
  pip install -r /tmp/requirements.txt && \
  # Cleanup
  apk del build && \
  rm -rf /tmp/build


# Install app source code
COPY . /tmp/build
RUN pip install -q /tmp/build && rm -rf /tmp/build

# Collect callico static files
RUN manage.py collectstatic --no-input

# Needed to use django-admin
ENV DJANGO_SETTINGS_MODULE=scorelib.settings

ENV PORT 80
EXPOSE 80