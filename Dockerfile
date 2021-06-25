# syntax=docker/dockerfile:1
FROM beaker.org/ai2/cuda11.2-ubuntu20.04

ARG DEBIAN_FRONTEND="noninteractive"

ENV PATH=/opt/miniconda3/bin:/opt/miniconda3/condabin:$PATH
ENV LD_LIBRARY_PATH=/usr/local/cuda/lib:/usr/local/cuda/lib64:$LD_LIBRARY_PATH

RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg

RUN pip install --upgrade pip
RUN pip install --upgrade setuptools
RUN pip install --upgrade youtube-dl

WORKDIR /audio
ENV PYTHONPATH=/audio:$PYTHONPATH
ENV MYHOME=/audio

COPY csv /audio/csv
COPY one_for_all.py /audio/one_for_all.py
COPY one_for_all.sh /audio/one_for_all.sh

RUN ls -la /audio/*

# https://stackoverflow.com/a/62313159
ENTRYPOINT [ "/bin/bash", "-l", "-c" ]
CMD ["ls", "./"]
