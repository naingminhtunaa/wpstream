import os
import subprocess
import urllib.parse
from flask import Flask, request, Response
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

# Host Website ကနေ လာတာပါလို့ ဟန်ဆောင်ပေးမယ့် Function
def get_referer(url):
    parsed = urllib.parse.urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}/"

@app.route('/stream.m3u8')
def generate_playlist():
    video_url = request.args.get('url')
    if not video_url:
        return "Missing URL", 400

    referer = get_referer(video_url)

    # ffprobe မှာ Referer header ထပ်ထည့်ထားပါတယ်
    probe_cmd = [
        'ffprobe', 
        '-user_agent', USER_AGENT,
        '-headers', f'Referer: {referer}\r\n',
        '-v', 'error', 
        '-show_entries', 'format=duration', 
        '-of', 'default=noprint_wrappers=1:nokey=1', 
        video_url
    ]
    
    try:
        duration_str = subprocess.check_output(probe_cmd, timeout=30).decode('utf-8').strip()
        duration = float(duration_str)
    except Exception as e:
        return f"Error probing video. URL blocked by Cloudflare/Firewall or not optimized. Error: {e}", 400

    segment_length = 10.0  
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
        m3u8_content.append(f"{base_url}/segment.ts?url={encoded_url}&start={current_time}&duration={seg_dur}")
        current_time += seg_dur

    m3u8_content.append("#EXT-X-ENDLIST")
    return Response("\n".join(m3u8_content), mimetype="application/vnd.apple.mpegurl")

@app.route('/segment.ts')
def get_segment():
    video_url = request.args.get('url')
    start = request.args.get('start')
    duration = request.args.get('duration')

    if not all([video_url, start, duration]):
        return "Missing parameters", 400

    referer = get_referer(video_url)

    # ffmpeg မှာလည်း Referer header ထပ်ထည့်ထားပါတယ်
    command = [
        'ffmpeg',
        '-user_agent', USER_AGENT,
        '-headers', f'Referer: {referer}\r\n',
        '-ss', str(start),    
        '-i', video_url,      
        '-t', str(duration),  
        '-codec', 'copy',     
        '-f', 'mpegts',       
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
