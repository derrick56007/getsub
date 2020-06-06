# [derrick56007/GetSub](https://github.com/Derrick56007/getsub)

![master](https://github.com/Derrick56007/getsub/workflows/master/badge.svg)

## Introduction

A small tool to download subtitles and sync automatically using Voice Activity Detection

- Docker Hub: https://hub.docker.com/r/derrick56007/getsub

## Usage 

First pull docker image
```
docker pull derrick56007/getsub:latest
```

Then run on movie or tv show of your choosing
```
docker run -tiv /$VIDEO_DIR:/files derrick56007/getsub:latest /files/$VIDEO_FILE.mp4 $LANG
```

## Example

```
docker pull derrick56007/getsub:latest
docker run -tiv /Users/derrick/videos:/files derrick56007/getsub:latest /files/Game.of.Thrones.S02E09.1080p.BluRay.x265.10bit.6CH.ReEnc-LUMI.mkv eng
```
