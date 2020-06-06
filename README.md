# [derrick56007/GetSub](https://github.com/Derrick56007/getsub)

![Docker Image CI](https://github.com/Derrick56007/getsub/workflows/Docker%20Image%20CI/badge.svg)

## Usage 

```
docker pull derrick56007/getsub:latest
docker run -tiv /$VIDEO_DIR:/files derrick56007/getsub:latest /files/$VIDEO_FILE.mp4 $LANG
```

## Example

```
docker pull derrick56007/getsub:latest
docker run -tiv /Users/derrick/videos:/files derrick56007/getsub:latest /files/Game.of.Thrones.S02E09.1080p.BluRay.x265.10bit.6CH.ReEnc-LUMI.mkv eng
```
