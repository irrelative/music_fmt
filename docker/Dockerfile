#Download base image ubuntu 24.04
FROM ubuntu:24.04

RUN apt-get update && apt-get install -y \
    cuetools \
    shntool \
    flac \
    lame \
    vim \
    ffmpeg \
    jq \
    python3 \
    python3-venv \
    python3-pip

# Create a virtual environment
ENV VIRTUAL_ENV=/opt/venv
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Install beets in the virtual environment
RUN pip install beets requests

# Set up beets configuration
RUN mkdir -p /root/.config/beets
COPY beets_config.yaml /root/.config/beets/config.yaml

COPY flac2mp3.sh /usr/local/bin/flac2mp3.sh
COPY flacue.py /usr/local/bin/flacue.py

# Set up environment variables
ENV PATH="/usr/local/bin:$PATH"
ENV BEETSDIR="/root/.config/beets"

