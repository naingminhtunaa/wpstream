FROM python:3.9-slim

# FFmpeg install လုပ်ခြင်း
RUN apt-get update && apt-get install -y ffmpeg

WORKDIR /app
COPY . /app
RUN pip install flask flask-cors requests gunicorn

CMD ["gunicorn", "--timeout", "300", "-b", "0.0.0.0:8080", "app:app"]
