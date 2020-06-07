GetSub
======

![master](https://github.com/Derrick56007/getsub/workflows/master/badge.svg)

Introduction
------------

Download subtitles in any language and sync automatically using Voice Activity Detection

Features
--------

- Supports 60 languages! The official list can be found [here](http://www.opensubtitles.org/addons/export_languages.php)
- Available as Docker image

Requirements
------------

- python3+
- ffmpeg
- gcc
- pip

Install
--------------

```
git clone https://github.com/Derrick56007/getsub.git
cd getsub/
apt-get install -y gcc ffmpeg
pip install -r requirements.txt

```

Usage
------------

```
python run.py files/$VIDEO_FILE.mp4 $LANG
```

Example
--------------

```
python run.py /Users/derrick/videos/Game.of.Thrones.S02E09.1080p.BluRay.x265.10bit.6CH.ReEnc-LUMI.mkv eng
```
GetSub Docker
=============

Requirements
------------

- Docker: https://docs.docker.com/get-docker/

Install
--------------

```
docker pull derrick56007/getsub:latest
```

Usage
------------

```
docker run -tiv /$VIDEO_DIR:/files derrick56007/getsub:latest /files/$VIDEO_FILE.mp4 $LANG
```

Example
--------------

```
docker run -tiv /Users/derrick/videos:/files derrick56007/getsub:latest /files/Game.of.Thrones.S02E09.1080p.BluRay.x265.10bit.6CH.ReEnc-LUMI.mkv eng
```
