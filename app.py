import os
from flask import Flask, request, Response, stream_with_context
from flask_cors import CORS
import subprocess

app = Flask(__name__)
CORS(app)

@app.route('/stream.m3u8')
def stream_m3u8():
    video_url = request.args.get('url')
    if not video_url:
        return "Missing video URL", 400

    # FFmpeg command ကို stream ပိုမြန်အောင် optimized လုပ်ထားပါတယ်
    command = [
        'ffmpeg',
        '-reconnect', '1',
        '-reconnect_streamed', '1',
        '-reconnect_delay_max', '5',
        '-i', video_url,
        '-codec', 'copy', # encoding မလုပ်ဘဲ တိုက်ရိုက်ကူးတဲ့အတွက် မြန်ပါတယ်
        '-f', 'hls',
        '-hls_time', '6',
        '-hls_list_size', '0',
        'pipe:1'
    ]

    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)

    def generate():
        try:
            while True:
                data = process.stdout.read(1024)
                if not data:
                    break
                yield data
        finally:
            process.kill() # Player ပိတ်လိုက်ရင် FFmpeg ကိုပါ ရပ်ပစ်ဖို့

    return Response(stream_with_context(generate()), mimetype='application/vnd.apple.mpegurl')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
