import os
import gc
import uuid
import requests
import json
import time
import asyncio
import edge_tts
from flask import Flask, render_template, request, send_file, jsonify
from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips
from deep_translator import GoogleTranslator
from urllib.parse import quote # Spaces aur symbols handle karne ke liye

app = Flask(__name__)

# ================= CONFIGURATION =================
# HD Animation Look ke liye optimize kiya hua suffix
STYLE_SUFFIX = ", high quality 3D animation style, Pixar inspired, vivid colors, cinematic lighting, 4k resolution, cartoon style"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, 'static')
GALLERY_JSON = os.path.join(BASE_DIR, 'gallery_data.json')

# Directories ensure karein
for f in ['images', 'audio', 'videos']:
    os.makedirs(os.path.join(STATIC_DIR, f), exist_ok=True)

# ================= UTILS =================

async def save_voice_edge(text, voice, save_path):
    """Microsoft Edge-TTS Logic"""
    try:
        communicate = edge_tts.Communicate(text, voice)
        await communicate.save(save_path)
    except Exception as e:
        print(f"Voice Gen Error: {e}")

def translate_text(text):
    """Hindi/Any to English Translation"""
    try:
        # Prompt chota rakhte hain taaki URL crash na ho (Max 200 chars)
        short_text = text[:200]
        return GoogleTranslator(source='auto', target='en').translate(short_text)
    except: 
        return text[:200]

def get_pollinations_image(prompt, save_path):
    """2025 Verified Image Generation with Integrity Check"""
    try:
        translated_prompt = translate_text(prompt)
        # Suffix ko simple aur effective rakhte hain
        final_prompt = f"{translated_prompt}, high quality 3D render, Pixar style, vivid colors, 4k"
        
        encoded_prompt = quote(final_prompt)
        seed = uuid.uuid4().int >> 100
        
        # 2025 ka sabse stable endpoint
        url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1024&height=1024&seed={seed}&nologo=true&model=flux"
        
        print(f"Requesting AI Image: {url[:100]}...")
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=120) # Timeout badha diya
        
        # INTEGRITY CHECK: Kya ye sach mein image hai?
        content_type = response.headers.get('Content-Type', '')
        
        if response.status_code == 200 and 'image' in content_type:
            # Check if file size is too small (e.g. less than 10KB is usually an error text)
            if len(response.content) > 10000:
                with open(save_path, 'wb') as f:
                    f.write(response.content)
                print(f"Success: Image saved ({len(response.content)} bytes)")
                return True
            else:
                print("Error: Received data is too small to be an image.")
                return False
        else:
            print(f"API Failed! Status: {response.status_code}, Content-Type: {content_type}")
            return False
            
    except Exception as e:
        print(f"System Error: {e}")
        return False
# ================= ROUTES =================

@app.route('/')
def home(): return render_template('index.html')

@app.route('/video-creator')
def video_creator_page(): return render_template('video_creator.html')

@app.route('/image-creator')
def image_creator_page(): return render_template('image_creator.html')

@app.route('/pricing')
def pricing(): return render_template('pricing.html')

@app.route('/about')
def about(): return render_template('about.html')

@app.route('/contact')
def contact(): return render_template('contact.html')

# ================= GALLERY SYSTEM =================

@app.route('/gallery/photos')
def photo_gallery():
    items = []
    if os.path.exists(GALLERY_JSON):
        try:
            with open(GALLERY_JSON, 'r') as f:
                all_data = json.load(f)
                items = [i for i in all_data if i.get('type') == 'photo']
        except: items = []
    return render_template('photo_gallery.html', items=items[::-1])

@app.route('/gallery/videos')
def video_gallery():
    items = []
    if os.path.exists(GALLERY_JSON):
        try:
            with open(GALLERY_JSON, 'r') as f:
                all_data = json.load(f)
                items = [i for i in all_data if i.get('type') == 'video']
        except: items = []
    return render_template('video_gallery.html', items=items[::-1])

# ================= API ENDPOINTS =================

@app.route('/generate-video', methods=['POST'])
def generate_video_api():
    full_story = request.form.get('prompt')
    selected_voice = request.form.get('voice', 'hi-IN-SwaraNeural')
    
    if not full_story: return jsonify({"error": "Prompt khali hai"}), 400

    # Story splitting logic
    scenes = [s.strip() for s in full_story.split('.') if len(s.strip()) > 5][:5]
    video_clips = []
    session_id = uuid.uuid4().hex[:6]
    
    try:
        for i, text in enumerate(scenes):
            print(f"Working on Scene {i+1}...")
            img_path = os.path.join(STATIC_DIR, 'images', f"vid_{session_id}_{i}.png")
            aud_path = os.path.join(STATIC_DIR, 'audio', f"aud_{session_id}_{i}.mp3")
            
            if not get_pollinations_image(text, img_path): continue
            
            asyncio.run(save_voice_edge(text, selected_voice, aud_path))
            
            audio = AudioFileClip(aud_path)
            clip = ImageClip(img_path).set_duration(audio.duration)
            clip = clip.resize(lambda t: 1 + 0.05 * t).set_position('center').set_audio(audio)
            video_clips.append(clip)
            gc.collect()

        if not video_clips: return jsonify({"error": "AI image generation failed"}), 500

        final_video = concatenate_videoclips(video_clips, method="compose")
        out_name = f"story_{session_id}.mp4"
        out_path = os.path.join(STATIC_DIR, 'videos', out_name)
        final_video.write_videofile(out_path, fps=24, codec="libx264")
        
        for c in video_clips: c.close()
        final_video.close()
        return jsonify({"video_url": f"/static/videos/{out_name}"})
    except Exception as e:
        print(f"Crash Logic: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/generate-image', methods=['POST'])
def generate_image_api():
    prompt = request.form.get('prompt')
    if not prompt: return jsonify({"error": "No prompt"}), 400

    img_name = f"art_{uuid.uuid4().hex[:8]}.png"
    img_path = os.path.join(STATIC_DIR, 'images', img_name)
    
    if get_pollinations_image(prompt, img_path):
        return jsonify({"image_url": f"/static/images/{img_name}"})
    return jsonify({"error": "AI Service unavailable, try again in 10s"}), 500

@app.route('/publish', methods=['POST'])
def publish():
    try:
        entry = {
            "id": uuid.uuid4().hex[:8],
            "type": request.form.get('type'),
            "title": request.form.get('title'),
            "description": request.form.get('description'),
            "tags": request.form.get('tags'),
            "file_url": request.form.get('file_url'),
            "timestamp": time.strftime("%Y-%m-%d %H:%M")
        }
        data = []
        if os.path.exists(GALLERY_JSON):
            with open(GALLERY_JSON, 'r') as f: data = json.load(f)
        data.append(entry)
        with open(GALLERY_JSON, 'w') as f: json.dump(data, f, indent=4)
        return jsonify({"success": True})
    except: return jsonify({"error": "JSON database error"}), 500

@app.route('/download/<filename>')
def download_file(filename):
    for folder in ['videos', 'images']:
        path = os.path.join(STATIC_DIR, folder, filename)
        if os.path.exists(path): return send_file(path, as_attachment=True)
    return "Not Found", 404

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000, use_reloader=False)
