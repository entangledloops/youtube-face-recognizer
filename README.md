# YouTube Face Recognizer

A Flask-based service that detects if a person from a reference image appears in a YouTube video.

## Description

This service allows you to upload a reference image of a person and provide a YouTube URL. It will then analyze the video to determine if the person appears in the video, returning the time and confidence level of any matches.

## Installation

### Option 1: Using Docker (Recommended)

Pull the pre-built Docker image and run it:

```bash
docker pull entangledloops/youtube-face-recognizer:latest
docker run -p 5005:5005 entangledloops/youtube-face-recognizer:latest
```

### Option 2: Local Installation

1. Clone this repository
2. Install the required dependencies:

```bash
pip install -r requirements.txt
```

3. Run the application:

```bash
python app.py
```

The server will be available at http://localhost:5005

## Usage

Send a POST request to the `/detect` endpoint with:
- `url`: YouTube video URL
- `image`: Reference image file

### Example

```bash
curl -X POST http://localhost:5005/detect \
  -F "url=https://www.youtube.com/watch?v=LmG2zpJZf0M" \
  -F "image=@otz.png"
```

### Response

The API returns a JSON response with:
- `face_present`: Boolean indicating if the face was found
- `video_url`: The URL of the analyzed video
- `match_frame`: (if found) The frame number where the match was found
- `match_distance`: (if found) The confidence level of the match (lower is better)
- `match_time_seconds`: (if found) The timestamp in the video where the match occurs

## Building From Source

You can build the Docker image yourself:

```bash
docker build -t youtube-face-recognizer .
docker run -p 5005:5005 youtube-face-recognizer
```