import os
import sys
import uuid
import shutil
import subprocess
import threading
from pathlib import Path
from flask import Flask, request, jsonify, render_template_string, send_from_directory, send_file

app = Flask(__name__)

BASE_DIR = Path(__file__).resolve().parent
BIN_DIR = BASE_DIR / "bin"
FFMPEG_BIN = str(BIN_DIR / "ffmpeg.exe") if (BIN_DIR / "ffmpeg.exe").exists() else "ffmpeg"
UPLOAD_FOLDER = BASE_DIR / "uploads"
OUTPUT_FOLDER = BASE_DIR / "compressed"
DESKTOP_FOLDER = Path.home() / "Desktop"

UPLOAD_FOLDER.mkdir(exist_ok=True)
OUTPUT_FOLDER.mkdir(exist_ok=True)

# Active compression jobs status tracking
jobs = {}

def format_size(bytes_val):
    for unit in ["B", "KB", "MB", "GB"]:
        if bytes_val < 1024.0:
            return f"{bytes_val:.2f} {unit}"
        bytes_val /= 1024.0
    return f"{bytes_val:.2f} TB"

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Video Compressor - Visually Lossless</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg: #0f172a;
            --card-bg: rgba(30, 41, 59, 0.7);
            --card-border: rgba(255, 255, 255, 0.1);
            --primary: #6366f1;
            --primary-hover: #4f46e5;
            --accent: #10b981;
            --text-main: #f8fafc;
            --text-muted: #94a3b8;
        }

        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
            font-family: 'Inter', sans-serif;
        }

        body {
            background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 100%);
            color: var(--text-main);
            min-height: 100vh;
            padding: 40px 20px;
            display: flex;
            flex-direction: column;
            align-items: center;
        }

        .container {
            max-width: 900px;
            width: 100%;
        }

        header {
            text-align: center;
            margin-bottom: 35px;
        }

        header h1 {
            font-size: 2.3rem;
            font-weight: 700;
            background: linear-gradient(to right, #818cf8, #c084fc);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 8px;
        }

        header p {
            color: var(--text-muted);
            font-size: 1.05rem;
        }

        .card {
            background: var(--card-bg);
            backdrop-filter: blur(16px);
            border: 1px solid var(--card-border);
            border-radius: 16px;
            padding: 28px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
            margin-bottom: 25px;
        }

        .drop-zone {
            border: 2px dashed rgba(99, 102, 241, 0.5);
            border-radius: 12px;
            padding: 45px 20px;
            text-align: center;
            cursor: pointer;
            transition: all 0.25s ease;
            background: rgba(99, 102, 241, 0.04);
        }

        .drop-zone:hover, .drop-zone.dragover {
            border-color: #818cf8;
            background: rgba(99, 102, 241, 0.12);
            transform: translateY(-2px);
        }

        .drop-zone svg {
            width: 50px;
            height: 50px;
            color: #818cf8;
            margin-bottom: 12px;
        }

        .drop-zone p {
            font-size: 1.05rem;
            color: var(--text-main);
            margin-bottom: 6px;
        }

        .drop-zone span {
            font-size: 0.85rem;
            color: var(--text-muted);
        }

        .file-info {
            display: none;
            margin-top: 15px;
            background: rgba(15, 23, 42, 0.6);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 10px;
            padding: 12px 18px;
            align-items: center;
            justify-content: space-between;
        }

        .file-info .name {
            font-weight: 500;
            color: #e2e8f0;
        }

        .file-info .size {
            font-size: 0.85rem;
            color: var(--accent);
            font-weight: 600;
        }

        .options-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }

        .form-group label {
            display: block;
            font-size: 0.85rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            color: var(--text-muted);
            margin-bottom: 8px;
        }

        select, input[type="range"] {
            width: 100%;
            background: rgba(15, 23, 42, 0.7);
            border: 1px solid var(--card-border);
            border-radius: 8px;
            padding: 10px 14px;
            color: var(--text-main);
            font-size: 0.95rem;
            outline: none;
        }

        select:focus {
            border-color: var(--primary);
        }

        .slider-wrap {
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .slider-val {
            font-weight: 600;
            color: #818cf8;
            min-width: 40px;
        }

        .checkbox-group {
            display: flex;
            align-items: center;
            gap: 10px;
            margin-top: 18px;
        }

        .checkbox-group input {
            width: 18px;
            height: 18px;
            accent-color: var(--primary);
            cursor: pointer;
        }

        .checkbox-group label {
            font-size: 0.95rem;
            cursor: pointer;
        }

        .btn {
            display: block;
            width: 100%;
            background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
            color: white;
            border: none;
            border-radius: 10px;
            padding: 15px;
            font-size: 1.05rem;
            font-weight: 600;
            cursor: pointer;
            margin-top: 24px;
            transition: all 0.2s ease;
            box-shadow: 0 4px 15px rgba(99, 102, 241, 0.4);
        }

        .btn:hover:not(:disabled) {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(99, 102, 241, 0.6);
        }

        .btn:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }

        .progress-box {
            display: none;
            margin-top: 20px;
        }

        .progress-bar-bg {
            background: rgba(15, 23, 42, 0.8);
            border-radius: 8px;
            height: 12px;
            overflow: hidden;
            border: 1px solid rgba(255, 255, 255, 0.05);
        }

        .progress-bar-fill {
            height: 100%;
            width: 100%;
            background: linear-gradient(90deg, #6366f1, #10b981, #6366f1);
            background-size: 200% 100%;
            animation: shimmer 1.5s infinite linear;
        }

        @keyframes shimmer {
            0% { background-position: 200% 0; }
            100% { background-position: -200% 0; }
        }

        .status-text {
            text-align: center;
            font-size: 0.9rem;
            color: var(--text-muted);
            margin-top: 10px;
        }

        .result-box {
            display: none;
            margin-top: 25px;
            padding: 20px;
            background: rgba(16, 185, 129, 0.08);
            border: 1px solid rgba(16, 185, 129, 0.3);
            border-radius: 12px;
        }

        .stats-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 15px;
            text-align: center;
            margin-bottom: 20px;
        }

        .stat-item {
            background: rgba(15, 23, 42, 0.5);
            padding: 12px;
            border-radius: 8px;
        }

        .stat-label {
            font-size: 0.75rem;
            color: var(--text-muted);
            text-transform: uppercase;
        }

        .stat-value {
            font-size: 1.25rem;
            font-weight: 700;
            color: var(--text-main);
            margin-top: 4px;
        }

        .stat-value.highlight {
            color: var(--accent);
        }

        .action-btns {
            display: flex;
            gap: 12px;
        }

        .btn-download {
            flex: 1;
            text-decoration: none;
            text-align: center;
            background: #10b981;
            color: white;
            padding: 12px;
            border-radius: 8px;
            font-weight: 600;
            transition: background 0.2s;
        }

        .btn-download:hover {
            background: #059669;
        }

        video {
            width: 100%;
            max-height: 420px;
            border-radius: 10px;
            background: black;
            margin-bottom: 15px;
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>⚡ Video Compressor Web UI</h1>
            <p>Reduce video file size by 50–75% with visually lossless clarity</p>
        </header>

        <div class="card">
            <div class="drop-zone" id="dropZone">
                <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                          d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"></path>
                </svg>
                <p><strong>Click to browse</strong> or drag & drop video file here</p>
                <span>Supports MP4, MKV, MOV, WEBM, AVI</span>
                <input type="file" id="fileInput" accept="video/*" style="display: none;">
            </div>

            <div class="file-info" id="fileInfo">
                <span class="name" id="fileName">video.mp4</span>
                <span class="size" id="fileSize">0 MB</span>
            </div>

            <div class="options-grid">
                <div class="form-group">
                    <label>Codec</label>
                    <select id="codecSelect">
                        <option value="av1" selected>AV1 (libsvtav1) - Smallest size & Pristine Quality</option>
                        <option value="hevc">H.265 / HEVC - Universal Device Playback</option>
                        <option value="h264">H.264 - Maximum Legacy Compatibility</option>
                    </select>
                </div>

                <div class="form-group">
                    <label>Quality Mode (CRF)</label>
                    <select id="qualityPreset">
                        <option value="visually_lossless" selected>Visually Lossless (Recommended)</option>
                        <option value="balanced">Balanced (Smaller Size)</option>
                        <option value="high_compression">High Compression (Lowest Size)</option>
                    </select>
                </div>
            </div>

            <div class="checkbox-group">
                <input type="checkbox" id="saveDesktop" checked>
                <label for="saveDesktop">Also save a copy directly to Desktop</label>
            </div>

            <button class="btn" id="startBtn" disabled>Start Compression</button>

            <div class="progress-box" id="progressBox">
                <div class="progress-bar-bg">
                    <div class="progress-bar-fill"></div>
                </div>
                <div class="status-text" id="statusText">Compressing video using AV1... please wait.</div>
            </div>

            <div class="result-box" id="resultBox">
                <video id="videoPreview" controls></video>
                <div class="stats-grid">
                    <div class="stat-item">
                        <div class="stat-label">Original Size</div>
                        <div class="stat-value" id="origSizeDisplay">0 MB</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-label">Compressed Size</div>
                        <div class="stat-value" id="compSizeDisplay">0 MB</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-label">Space Saved</div>
                        <div class="stat-value highlight" id="savedDisplay">0%</div>
                    </div>
                </div>

                <div class="action-btns">
                    <a href="#" class="btn-download" id="downloadBtn" download>Download Compressed Video</a>
                </div>
            </div>
        </div>
    </div>

    <script>
        const dropZone = document.getElementById('dropZone');
        const fileInput = document.getElementById('fileInput');
        const fileInfo = document.getElementById('fileInfo');
        const fileName = document.getElementById('fileName');
        const fileSize = document.getElementById('fileSize');
        const startBtn = document.getElementById('startBtn');
        const progressBox = document.getElementById('progressBox');
        const statusText = document.getElementById('statusText');
        const resultBox = document.getElementById('resultBox');
        const codecSelect = document.getElementById('codecSelect');
        const qualityPreset = document.getElementById('qualityPreset');
        const saveDesktop = document.getElementById('saveDesktop');
        const videoPreview = document.getElementById('videoPreview');
        const downloadBtn = document.getElementById('downloadBtn');

        let selectedFile = null;

        dropZone.addEventListener('click', () => fileInput.click());

        fileInput.addEventListener('change', (e) => {
            if (e.target.files.length > 0) {
                handleFile(e.target.files[0]);
            }
        });

        dropZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            dropZone.classList.add('dragover');
        });

        dropZone.addEventListener('dragleave', () => dropZone.classList.remove('dragover'));

        dropZone.addEventListener('drop', (e) => {
            e.preventDefault();
            dropZone.classList.remove('dragover');
            if (e.dataTransfer.files.length > 0) {
                handleFile(e.dataTransfer.files[0]);
            }
        });

        function formatBytes(bytes) {
            if (bytes === 0) return '0 B';
            const k = 1024;
            const sizes = ['B', 'KB', 'MB', 'GB'];
            const i = Math.floor(Math.log(bytes) / Math.log(k));
            return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
        }

        function handleFile(file) {
            selectedFile = file;
            fileName.textContent = file.name;
            fileSize.textContent = formatBytes(file.size);
            fileInfo.style.display = 'flex';
            startBtn.disabled = false;
            resultBox.style.display = 'none';
        }

        startBtn.addEventListener('click', async () => {
            if (!selectedFile) return;

            startBtn.disabled = true;
            progressBox.style.display = 'block';
            resultBox.style.display = 'none';
            statusText.textContent = `Uploading and compressing "${selectedFile.name}" with ${codecSelect.value.toUpperCase()}...`;

            const formData = new FormData();
            formData.append('video', selectedFile);
            formData.append('codec', codecSelect.value);
            formData.append('quality', qualityPreset.value);
            formData.append('save_desktop', saveDesktop.checked ? 'true' : 'false');

            try {
                const res = await fetch('/api/compress', {
                    method: 'POST',
                    body: formData
                });

                const data = await res.json();
                if (!res.ok || data.error) {
                    alert('Compression failed: ' + (data.error || 'Server error'));
                    progressBox.style.display = 'none';
                    startBtn.disabled = false;
                    return;
                }

                // Poll job
                pollJob(data.job_id);
            } catch (err) {
                alert('Request failed: ' + err.message);
                progressBox.style.display = 'none';
                startBtn.disabled = false;
            }
        });

        async function pollJob(jobId) {
            const interval = setInterval(async () => {
                try {
                    const res = await fetch(`/api/status/${jobId}`);
                    const data = await res.json();

                    if (data.status === 'processing') {
                        statusText.textContent = data.message || 'Compressing video...';
                    } else if (data.status === 'done') {
                        clearInterval(interval);
                        progressBox.style.display = 'none';
                        startBtn.disabled = false;
                        showResult(data);
                    } else if (data.status === 'error') {
                        clearInterval(interval);
                        progressBox.style.display = 'none';
                        startBtn.disabled = false;
                        alert('Error: ' + data.message);
                    }
                } catch (e) {
                    clearInterval(interval);
                    progressBox.style.display = 'none';
                    startBtn.disabled = false;
                }
            }, 1000);
        }

        function showResult(data) {
            resultBox.style.display = 'block';
            document.getElementById('origSizeDisplay').textContent = data.orig_size_str;
            document.getElementById('compSizeDisplay').textContent = data.comp_size_str;
            document.getElementById('savedDisplay').textContent = `${data.saved_percent}% (${data.saved_str})`;

            videoPreview.src = `/download/${data.output_filename}`;
            downloadBtn.href = `/download/${data.output_filename}`;
            downloadBtn.download = data.output_filename;
        }
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

def run_compression_worker(job_id, in_path, out_path, desktop_path, codec, quality_preset):
    jobs[job_id]["status"] = "processing"
    jobs[job_id]["message"] = "Encoding video with visually lossless parameters..."
    
    # Configure CRF
    if codec == "av1":
        encoder = "libsvtav1"
        crf = 25 if quality_preset == "visually_lossless" else (27 if quality_preset == "balanced" else 30)
        preset = "5"
        pix_fmt = ["-pix_fmt", "yuv420p10le"]
    elif codec == "hevc":
        encoder = "libx265"
        crf = 22 if quality_preset == "visually_lossless" else (25 if quality_preset == "balanced" else 28)
        preset = "slow"
        pix_fmt = ["-pix_fmt", "yuv420p"]
    else:
        encoder = "libx264"
        crf = 19 if quality_preset == "visually_lossless" else (22 if quality_preset == "balanced" else 25)
        preset = "slow"
        pix_fmt = ["-pix_fmt", "yuv420p"]

    cmd = [
        FFMPEG_BIN,
        "-y",
        "-i", str(in_path),
        "-c:v", encoder,
        "-crf", str(crf),
        "-preset", preset,
        *pix_fmt,
        "-c:a", "copy",
        "-map_metadata", "0",
        str(out_path)
    ]
    
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if res.returncode != 0:
        jobs[job_id]["status"] = "error"
        jobs[job_id]["message"] = res.stderr[-500:] if res.stderr else "Compression failed."
        return

    if desktop_path:
        shutil.copy2(str(out_path), str(desktop_path))

    orig_size = in_path.stat().st_size
    comp_size = out_path.stat().st_size
    saved_bytes = max(0, orig_size - comp_size)
    saved_pct = round((saved_bytes / orig_size) * 100, 1) if orig_size > 0 else 0

    jobs[job_id].update({
        "status": "done",
        "orig_size": orig_size,
        "comp_size": comp_size,
        "orig_size_str": format_size(orig_size),
        "comp_size_str": format_size(comp_size),
        "saved_bytes": saved_bytes,
        "saved_str": format_size(saved_bytes),
        "saved_percent": saved_pct,
        "output_filename": out_path.name
    })

@app.route('/api/compress', methods=['POST'])
def api_compress():
    if 'video' not in request.files:
        return jsonify({"error": "No video file provided"}), 400
    
    file = request.files['video']
    if not file.filename:
        return jsonify({"error": "No file selected"}), 400

    codec = request.form.get('codec', 'av1')
    quality = request.form.get('quality', 'visually_lossless')
    save_desktop = request.form.get('save_desktop') == 'true'

    job_id = str(uuid.uuid4())
    in_ext = Path(file.filename).suffix or ".mp4"
    in_file = UPLOAD_FOLDER / f"upload_{job_id}{in_ext}"
    file.save(str(in_file))

    stem = Path(file.filename).stem
    out_name = f"{stem}_compressed_{codec}.mp4"
    out_file = OUTPUT_FOLDER / out_name
    desktop_file = (DESKTOP_FOLDER / out_name) if save_desktop else None

    jobs[job_id] = {
        "status": "queued",
        "filename": file.filename,
        "job_id": job_id
    }

    t = threading.Thread(
        target=run_compression_worker,
        args=(job_id, in_file, out_file, desktop_file, codec, quality)
    )
    t.daemon = True
    t.start()

    return jsonify({"job_id": job_id, "status": "queued"})

@app.route('/api/status/<job_id>')
def api_status(job_id):
    job = jobs.get(job_id)
    if not job:
        return jsonify({"status": "not_found"}), 404
    return jsonify(job)

@app.route('/download/<filename>')
def download(filename):
    return send_from_directory(OUTPUT_FOLDER, filename, as_attachment=False)

if __name__ == '__main__':
    port = 5000
    print(f"\n=======================================================")
    print(f" Video Compressor Web UI running at: http://localhost:{port}")
    print(f"=======================================================\n")
    app.run(host='0.0.0.0', port=port, debug=False)
