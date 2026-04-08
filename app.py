import os
import subprocess
import urllib.parse
from flask import Flask, request, Response
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route('/stream.m3u8')
def generate_playlist():
    video_url = request.args.get('url')
    if not video_url:
        return "Missing URL", 400

    # 1. FFprobe သုံးပြီး ဗီဒီယိုရဲ့ အရှည် (Duration) ကို အရင်မြန်မြန်လှမ်းယူမယ်
    probe_cmd = [
        'ffprobe', '-v', 'error', 
        '-show_entries', 'format=duration', 
        '-of', 'default=noprint_wrappers=1:nokey=1', 
        video_url
    ]
    try:
        # ၁၀ စက္ကန့်အတွင်း Duration မရရင် error ပြမယ်
        duration_str = subprocess.check_output(probe_cmd, timeout=15).decode('utf-8').strip()
        duration = float(duration_str)
    except Exception as e:
        return f"Error probing video. URL might be blocked or invalid. Error: {e}", 400

    # 2. M3U8 Playlist (စာသား) ကို Dynamic ဖန်တီးမယ်
    segment_length = 10.0  # တစ်ပိုင်းကို ၁၀ စက္ကန့်ထားမယ်
    m3u8_content = [
        "#EXTM3U",
        "#EXT-X-VERSION:3",
        f"#EXT-X-TARGETDURATION:{int(segment_length)}",
        "#EXT-X-MEDIA-SEQUENCE:0"
    ]

    base_url = request.host_url.rstrip('/')
    encoded_url = urllib.parse.quote(video_url)

    current_time = 0
    while current_time < duration:
        seg_dur = min(segment_length, duration - current_time)
        m3u8_content.append(f"#EXTINF:{seg_dur:.6f},")
        # Video အပိုင်းလေးတွေကို လှမ်းတောင်းမယ့် URL ကို playlist ထဲထည့်မယ်
        m3u8_content.append(f"{base_url}/segment.ts?url={encoded_url}&start={current_time}&duration={seg_dur}")
        current_time += seg_dur

    m3u8_content.append("#EXT-X-ENDLIST")
    
    # Text အနေနဲ့ Player ဆီ ချက်ချင်း ပို့ပေးလိုက်မယ်
    return Response("\n".join(m3u8_content), mimetype="application/vnd.apple.mpegurl")

@app.route('/segment.ts')
def get_segment():
    video_url = request.args.get('url')
    start = request.args.get('start')
    duration = request.args.get('duration')

    if not all([video_url, start, duration]):
        return "Missing parameters", 400

    # 3. Player က တောင်းတဲ့ ၁၀ စက္ကန့်စာ အပိုင်းလေးကိုပဲ FFmpeg နဲ့ ဖြတ်ပြီး ပို့မယ်
    command = [
        'ffmpeg',
        '-ss', str(start),    # စတင်မယ့် အချိန်
        '-i', video_url,      # မူရင်း Video URL
        '-t', str(duration),  # လိုချင်တဲ့ အရှည် (၁၀ စက္ကန့်)
        '-codec', 'copy',     # အရည်အသွေး မကျအောင် Copy ကူးမယ်
        '-f', 'mpegts',       # HLS format (.ts) အနေနဲ့ ထုတ်မယ်
        'pipe:1'
    ]

    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)

    def generate():
        try:
            while True:
                data = process.stdout.read(8192)
                if not data:
                    break
                yield data
        finally:
            process.kill()

    return Response(generate(), mimetype='video/MP2T')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
