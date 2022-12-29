FROM python:3.11-slim

RUN apt-get -qq update \
    && DEBIAN_FRONTEND=noninteractive apt-get -qq install \
    gcc ffmpeg

RUN rm -rf /var/lib/apt/lists/*

RUN pip install -qq numpy pandas srt webrtcvad progress tqdm joblib 

WORKDIR /app

COPY . .

ENTRYPOINT ["python", "run.py"]
