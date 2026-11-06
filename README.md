# Automated Radio Contest Transcriber & Submitter (`Radio-Transcriber`)

A Dockerized Python automation service that monitors live radio streams (`streamtheworld.com`), records rolling audio segments via `ffmpeg`, transcribes broadcasts using **OpenAI Whisper (GPU/PyTorch)**, detects contest keywords, sends real-time alerts with audio attachments to **Discord**, and automatically submits contest entries via **Playwright** (`submittal.py`).

---

## Features

- **Continuous Radio Stream Capture (`radio.py`)**:
  - Connects to live radio streams (`CHSUFMAAC.pls` / `streamtheworld.com`), validates stream health, and slices audio into rolling clips for low-latency processing.
- **AI Speech-to-Text (`whisper` + `torch`)**:
  - Runs OpenAI Whisper locally (with CUDA acceleration support) to transcribe radio segments into timestamped text logs.
- **Keyword Detection & Discord Alerts**:
  - Scans transcriptions for target trigger phrases (e.g., `"keyword"`, `"code word"`, `"text"`).
  - Immediately posts rich Discord webhook embeds along with the matching `.mp3`/`.wav` audio clip and transcript snippet.
- **Automated Contest Entry (`submittal.py`, `runner.py`)**:
  - Launches headless Playwright browser sessions (`ContestEntryBot`) to fill out and submit online radio contest forms when a keyword is detected, saving confirmation screenshots to `screenshots/`.

---

## Project Structure

```text
Radio-Transcriber/
├── radio.py               # RadioListener class: stream capture, Whisper STT & Discord alerts
├── submittal.py           # Playwright ContestEntryBot for automated web form submission
├── runner.py              # Scheduled orchestration entrypoint
├── CHSUFMAAC.pls          # StreamTheWorld playlist definition
├── dockerfile             # Container build definition with ffmpeg, PyTorch & Playwright
├── init.sh                # Container startup script
├── uwsgi.ini              # uWSGI configuration
└── requirements.txt       # Python dependencies (whisper, torch, discord, playwright, schedule)
```

---

## Usage

### Run Locally

```bash
python3 -m venv env
source env/bin/activate
pip install -r requirements.txt
playwright install chromium
python runner.py
```

### Run with Docker

```bash
docker build -f dockerfile -t radio-transcriber .
docker run -d --gpus all --name radio-transcriber radio-transcriber
```

---

## Credits, Acknowledgments & External Sources

- **[OpenAI Whisper](https://github.com/openai/whisper)** *(MIT License)*  
  Open-source neural speech recognition model by **OpenAI**, used in `radio.py` for local automated transcription of recorded radio broadcast segments.
- **[PyTorch (`torch`, `torchaudio`, `torchvision`)](https://github.com/pytorch/pytorch)** *(BSD-3-Clause License)*  
  Deep learning framework by the **PyTorch Foundation / Meta AI** providing CUDA GPU acceleration for Whisper inference.
- **[Microsoft Playwright for Python](https://github.com/microsoft/playwright-python)** *(Apache-2.0 License)*  
  Used by `ContestEntryBot` in `submittal.py` to automate headless browser contest form submissions and capture confirmation screenshots.
- **[`discord.py`](https://github.com/Rapptz/discord.py)** *(MIT License)*  
  Created by **Danny (`Rapptz`)**, used for sending real-time keyword detection embeds and audio clip attachments to Discord webhooks.
- **[FFmpeg](https://github.com/FFmpeg/FFmpeg)** *(LGPL / GPL)*  
  Used via `subprocess` to capture and segment live `streamtheworld.com` AAC/MP3 audio streams.
