GetSub
======

![master](https://github.com/Derrick56007/getsub/workflows/master/badge.svg)

Introduction
------------

Download subtitles in any language and sync automatically using Voice Activity Detection

Requirements
------------

- Docker: https://docs.docker.com/get-docker/

Install
-------

```
docker pull derrick56007/getsub:latest
```

Usage
-----

```
docker run -tiv /$VIDEO_DIR:/files derrick56007/getsub:latest /files/$VIDEO_FILE.mp4 $LANG
```

Example
-------

```
docker run -tiv /Users/derrick/videos:/files derrick56007/getsub:latest /files/Game.of.Thrones.S02E09.1080p.BluRay.x265.10bit.6CH.ReEnc-LUMI.mkv eng
```
