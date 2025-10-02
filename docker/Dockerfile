FROM python:3.12-alpine

LABEL description="Senotype Editor"

# Set up environment variables for Python
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Create and set the working directory
WORKDIR /usr/src/app

COPY . .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Specify the command to run on container start
CMD ["python", "/usr/src/app/app.py"]