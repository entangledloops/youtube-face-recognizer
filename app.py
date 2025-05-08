import os
import uuid
import face_recognition
import cv2
import numpy as np
from flask import Flask, request, jsonify
from yt_dlp import YoutubeDL

app = Flask(__name__)
UPLOAD_DIR = "temp"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Download YouTube video to a temp file
def download_video(url, output_path):
    ydl_opts = {
        'format': 'mp4',
        'outtmpl': output_path,
        'quiet': True,
        'no_warnings': True
    }
    with YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

# Check if influencer face is in video
def detect_face_in_video(video_path, reference_encoding, frame_skip=30, threshold=0.6):
    video = cv2.VideoCapture(video_path)
    frame_count = 0
    face_found = False
    
    print(f"Starting video analysis with threshold: {threshold}")

    while True:
        ret, frame = video.read()
        if not ret:
            break

        if frame_count % frame_skip == 0:
            try:
                # Convert BGR to RGB
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                
                # Find all face locations in the frame
                face_locations = face_recognition.face_locations(rgb_frame, model="hog")
                
                if face_locations:
                    # Create face encodings
                    face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)
                    
                    # Check if any face matches the reference
                    for face_encoding in face_encodings:
                        # Calculate face similarity
                        matches = face_recognition.compare_faces([reference_encoding], face_encoding, tolerance=threshold)
                        
                        # Alternative method using distance
                        face_distances = face_recognition.face_distance([reference_encoding], face_encoding)
                        distance = face_distances[0]
                        
                        print(f"Frame {frame_count}: Face found with distance {distance}")
                        
                        if matches[0] or distance < threshold:
                            print(f"Match found at frame {frame_count} with distance {distance}")
                            face_found = True
                            video.release()
                            return True
                
            except Exception as e:
                print(f"Error processing frame {frame_count}: {str(e)}")
                # Continue processing other frames
        
        frame_count += 1
        
        # Safety check for very long videos
        if frame_count > 10000:  # Limit to ~5-6 minutes of video at 30fps
            break

    video.release()
    print(f"Video analysis complete, processed {frame_count} frames, face found: {face_found}")
    return face_found

@app.route("/detect", methods=["POST"])
def detect():
    if 'url' not in request.form or 'image' not in request.files:
        return jsonify({"error": "Missing 'url' or 'image' in request"}), 400

    video_url = request.form['url']
    image_file = request.files['image']

    # Save temp files
    temp_id = str(uuid.uuid4())
    video_path = os.path.join(UPLOAD_DIR, f"{temp_id}.mp4")
    image_path = os.path.join(UPLOAD_DIR, f"{temp_id}.jpg")

    try:
        image_file.save(image_path)
        print(f"Downloading video from: {video_url}")
        download_video(video_url, video_path)
        print("Video download complete")

        # Load reference image and find face encodings
        print("Processing reference image")
        try:
            # Load the image as RGB (face_recognition expects RGB)
            reference_image = face_recognition.load_image_file(image_path)
            
            # Ensure the image is in the correct format
            if reference_image.shape[2] != 3:
                return jsonify({"error": "Reference image must be RGB"}), 400
                
            # Find faces in reference image
            print("Detecting faces in reference image")
            face_locations = face_recognition.face_locations(reference_image, model="hog")
            
            if not face_locations:
                return jsonify({"error": "No face found in reference image"}), 400
            
            print(f"Found {len(face_locations)} faces in reference image")
            
            # Get face encodings
            encodings = face_recognition.face_encodings(reference_image, face_locations)
            
            if not encodings or len(encodings) == 0:
                return jsonify({"error": "Could not compute face encoding from reference image"}), 400
                
            reference_encoding = encodings[0]
            print("Reference face encoding created successfully")
            
        except Exception as e:
            print(f"Error in reference image processing: {str(e)}")
            return jsonify({"error": f"Error processing reference image: {str(e)}"}), 500

        # Use a less strict threshold (higher value = more permissive)
        threshold = 0.55
        print(f"Running face detection with threshold {threshold}")
        found = detect_face_in_video(video_path, reference_encoding, threshold=threshold)

        return jsonify({
            "face_present": found,
            "video_url": video_url
        })

    except Exception as e:
        print(f"Error in detect endpoint: {str(e)}")
        return jsonify({"error": str(e)}), 500

    finally:
        # Cleanup
        for f in [video_path, image_path]:
            if os.path.exists(f):
                os.remove(f)

if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True, port=5005)
