#Download base image ubuntu 22.04
FROM ubuntu:22.04

RUN apt-get update
RUN apt-get install -y cuetools shntool flac lame vim ffmpeg jq python3 python3-pip
RUN pip3 install beets

# Set up beets configuration
RUN mkdir -p /root/.config/beets
COPY beets_config.yaml /root/.config/beets/config.yaml

COPY flac2mp3.sh /usr/local/bin/flac2mp3.sh
COPY flacue.py /usr/local/bin/flacue.py

# Set up environment variables
ENV PATH="/usr/local/bin:${PATH}"
ENV BEETSDIR="/root/.config/beets"

