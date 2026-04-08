FROM python:3.9-slim

# FFmpeg ကို Install လုပ်မယ်
RUN apt-get update && apt-get install -y ffmpeg

WORKDIR /app
COPY . /app

# လိုအပ်တဲ့ libraries တွေသွင်းမယ်
RUN pip install -r requirements.txt

# Async Worker (gevent) ကိုသုံးပြီး Server ကို run မယ်
CMD ["gunicorn", "-k", "gevent", "--worker-connections", "100", "--timeout", "120", "-b", "0.0.0.0:8080", "app:app"]
