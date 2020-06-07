GetSub
======

![master](https://github.com/Derrick56007/getsub/workflows/master/badge.svg)

Introduction
------------

**GetSub** is a tool written in Python to help you **download subtitles in any language** and **sync automatically** using Voice Activity Detection. 

Subtitle search utilizes the [OpenSubtitleDownload.py](https://github.com/emericg/OpenSubtitlesDownload) script written by [emericg](https://github.com/emericg) to precisely **identifying your video files** and download the correct subtitle. The subtitles search and download server is [opensubtitles.org](https://www.opensubtitles.org).

Features
--------

- Supports 60 languages! The official list can be found [here](http://www.opensubtitles.org/addons/export_languages.php)
- Available as Docker [image](https://hub.docker.com/r/derrick56007/getsub)

Requirements
------------

- python3+
- ffmpeg
- gcc
- pip

or if Docker is prefered:

- Docker: https://docs.docker.com/get-docker/

Install
--------------

```
git clone https://github.com/Derrick56007/getsub.git
cd getsub/
apt-get install -y gcc ffmpeg
pip install -r requirements.txt
```

Docker:

```
docker pull derrick56007/getsub:latest
```

Usage
------------

```
python run.py files/$VIDEO_FILE.mp4 $LANG
```

Docker:

```
docker run -tiv /$VIDEO_DIR:/files derrick56007/getsub:latest /files/$VIDEO_FILE.mp4 $LANG
```

Example
--------------

```
python run.py /Users/derrick/videos/Game.of.Thrones.S02E09.1080p.BluRay.x265.10bit.6CH.ReEnc-LUMI.mkv eng
```

Docker:

```
docker run -tiv /Users/derrick/videos:/files derrick56007/getsub:latest /files/Game.of.Thrones.S02E09.1080p.BluRay.x265.10bit.6CH.ReEnc-LUMI.mkv eng
```

Credits
-------
This project would not be possible without the following libraries:

- [ffmpeg](https://ffmpeg.org)
- [numpy](https://numpy.org)
- [srt](https://github.com/cdown/srt)
- [progress](https://github.com/verigak/progress/)
- [webrtcvad](https://github.com/wiseman/py-webrtcvad)
