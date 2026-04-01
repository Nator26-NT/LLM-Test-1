# NexEra AI-Generated 3D Training Content Pipeline

A Flask web application that turns text descriptions or images into interactive 3D models with educational summaries – all using local AI models (no API keys required).

## Features
- **Input:** Text description or image upload.
- **AI Classification:** Zero‑shot classification to detect object type (`hard_hat`, `wrench`, `safety_cone`, `safety_glasses`, `generic`).
- **AI Summarization:** Educational summary generated using T5‑small.
- **3D Model Generation:** Procedural mesh created based on the detected type, then centered and scaled.
- **GLB Export:** Model saved as a binary glTF file.
- **Interactive Viewer:** Embedded Three.js viewer with orbit controls (rotate, pan, zoom).
- **Fully Local:** No external API calls – models run on your machine.

## How It Works
1. User submits a description or image.
2. The app uses a zero‑shot classifier to determine the object type.
3. A T5 model generates a short educational summary.
4. A 3D mesh is created (hard hat, wrench, etc.) and exported to GLB.
5. The model is displayed in an interactive Three.js scene.

## Installation

### Prerequisites
- Python 3.9 or higher
- Pip package manager

### Step 1: Clone or download the project
Place all files (`app.py`, `generator.py`, `templates/`, `static/`) in a folder.

### Step 2: Install dependencies
Create a virtual environment (recommended) and install the required packages:

```bash
pip install -r requirements.txt