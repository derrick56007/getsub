FROM derrick56007/getsub:base

WORKDIR /app
COPY src/ /app
COPY run.py /app

ENTRYPOINT ["python", "run.py"]
