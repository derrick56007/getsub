FROM python:3.11.1-slim

RUN apt-get -qq update \
    && DEBIAN_FRONTEND=noninteractive apt-get -qq install \
    gcc ffmpeg

RUN rm -rf /var/lib/apt/lists/*

RUN pip install -qq numpy srt webrtcvad tqdm

WORKDIR /app

COPY . .

ENTRYPOINT ["python", "run.py"]
