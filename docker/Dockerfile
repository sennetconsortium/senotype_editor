FROM sennet/api-base-image:1.4.0

LABEL description="Senotype Editor"

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

RUN chown -R codcc:codcc /usr/src/app

USER codcc

# Specify the command to run on container start
ENTRYPOINT ["uwsgi", "--ini", "/usr/src/app/uwsgi.ini"]
