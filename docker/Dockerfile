FROM sennet/api-base-image:1.4.1

LABEL description="Senotype Editor"

ARG HOST_GID
ARG HOST_UID

# Set up environment variables for Python
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Create and set the working directory
WORKDIR /usr/src/app

EXPOSE 5010 5010

USER root

COPY ./app .

RUN apt-get update -y && \
    apt-get dist-upgrade -y

# Install dependencies
RUN pip install --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt && \
    rm requirements.txt

# Modify the UID and GID of codcc to match the host
RUN groupmod --gid $HOST_GID codcc && \
    usermod --uid $HOST_UID codcc

RUN mkdir -p /usr/src/app/log && \
    chown -R codcc:codcc /usr/src/app

USER codcc

# Specify the command to run on container start
ENTRYPOINT ["uwsgi", "--ini", "/usr/src/app/uwsgi.ini"]
