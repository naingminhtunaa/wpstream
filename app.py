import os
from flask import Flask, request, Response, stream_with_context
from flask_cors import CORS
import requests
import subprocess

app = Flask(__name__)
CORS(app)  # WordPress ကနေ လှမ်းခေါ်လို့ရအောင် CORS allow လုပ်ခြင်း

@app.route('/stream.m3u8')
def stream_m3u8():
    video_url = request.args.get('url')
    if not video_url:
        return "Missing video URL", 400

    # FFmpeg သုံးပြီး MP4 ကို HLS (m3u8) အဖြစ် Real-time ပြောင်းလဲခြင်း
    command = [
        'ffmpeg',
        '-i', video_url,
        '-codec:', 'copy', # Video quality မကျအောင် မူရင်းအတိုင်း copy ကူးခြင်း
        '-start_number', '0',
        '-hls_time', '10',
        '-hls_list_size', '0',
        '-f', 'hls',
        'pipe:1' # Output ကို output stream ဆီ တိုက်ရိုက်ပို့ခြင်း
    ]

    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    def generate():
        for line in process.stdout:
            yield line

    return Response(stream_with_context(generate()), mimetype='application/vnd.apple.mpegurl')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
