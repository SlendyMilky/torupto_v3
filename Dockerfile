FROM alpine:latest

# Configure timezone and install dependencies
RUN apk update && \
    apk upgrade && \
    apk add --no-cache \
    htop \
    tzdata \
    python3 \
    gcc \
    musl-dev \
    linux-headers \
    build-base \
    python3-dev \
    py3-pip && \
    mkdir /torupto && \
    cp /usr/share/zoneinfo/Europe/Zurich /etc/localtime && \
    echo "Europe/Zurich" > /etc/timezone && \
    ln -sf /usr/bin/python3 /usr/bin/python && \
    pip install --no-cache --upgrade pip setuptools --break-system-packages

# Install python package dependencies
WORKDIR /torupto/
COPY . /torupto/
RUN pip install python-dotenv --break-system-packages && \
    pip install -r requirements.txt --break-system-packages

# Run the application
CMD ["python3", "/torupto/torupto_v3.py"]
