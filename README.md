# High-Quality Video Compressor (Web UI & CLI)

A ready-to-use, high-efficiency video compressor that reduces file sizes by **50% to 75%** while keeping **visual clarity indistinguishable from the original**.

Works **locally on your PC** (CLI / Drag & Drop / Local Server) and **in the Cloud on Vercel** (In-Browser WebAssembly).

---

## 🌐 Deploy to Vercel

This repository is pre-configured for **1-click zero-config Vercel deployment**:

1. Push this repo to GitHub.
2. In your [Vercel Dashboard](https://vercel.com), click **Add New Project** and select this repository.
3. Click **Deploy** (No special build commands needed!).

### 💡 Why this works seamlessly on Vercel:
* **No Serverless Timeout Limits:** Standard Vercel Serverless functions time out after 10–15 seconds and have a 4.5 MB upload limit.
* **Client-Side WebAssembly (FFmpeg.wasm):** When deployed on Vercel, compression runs **100% inside the user's browser**. Your videos never upload to a server, meaning **no file size limits**, **unlimited processing time**, and **complete privacy**.
* **COOP/COEP Headers:** Pre-configured in `vercel.json` to enable high-speed multi-threaded WebAssembly in modern browsers.

---

## 💻 Local Usage on PC (Desktop / CLI)

When running locally on your computer, the tool uses the bundled native **FFmpeg 9.0.2** and **HandBrake CLI** for maximum hardware-accelerated encoding speed.

### Method 1: Web UI in Browser
Double-click `run_web_ui.bat` (or run `python app.py`) to launch the local web server at `http://localhost:5000`.

### Method 2: Drag & Drop (Windows)
Drag any video file or folder directly onto `compress.bat`. The compressed files will automatically appear in `compressed/`.

### Method 3: Terminal CLI (`compress.py`)

```bash
# Compress a single video (Default: AV1, visually lossless CRF 26)
python compress.py -i "path/to/video.mp4"

# Compress an entire folder of videos
python compress.py -i "C:\Videos" -o "C:\Videos\Compressed"

# Compress with H.265 / HEVC (for Smart TVs and older devices)
python compress.py -i "video.mp4" -c hevc

# Run a quick built-in test
python compress.py --test
```

---

## ⚙️ How "Same Clarity with Smaller Size" Works

Standard video encoders compress uniformly, often wasting megabytes on static scenes. This tool uses **Constant Rate Factor (CRF)** encoding:

| Codec | Setting | Visual Quality | Size Reduction | Compatibility |
| :--- | :--- | :--- | :--- | :--- |
| **AV1 (`libsvtav1`)** | `CRF 25-26` | Visually Lossless | **50% – 75%** | Modern PCs, Phones, Browsers |
| **H.265 / HEVC (`libx265`)** | `CRF 22-23` | Visually Lossless | **40% – 60%** | Universal (Smart TVs, Apple devices) |
| **H.264 (`libx264`)** | `CRF 20-22` | High Quality | **30% – 50%** | 100% Universal Compatibility |

> **Audio Quality:** Original audio tracks are copied bit-for-bit (`-c:a copy`) with zero re-encoding loss.
