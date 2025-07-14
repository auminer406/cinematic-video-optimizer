
from http.server import BaseHTTPRequestHandler
import json
import cloudinary
import cloudinary.uploader
import os
import tempfile
import base64

# Configure Cloudinary
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET")
)

def generate_embed_code(mp4_url, webm_url, poster_url):
    return f"""<!-- Cinematic Landing Page Video -->
<div class="cinematic-hero" style="position: relative; width: 100%; height: 100vh; overflow: hidden;">
  <video 
    style="position: absolute; top: 50%; left: 50%; min-width: 100%; min-height: 100%; width: auto; height: auto; transform: translate(-50%, -50%); object-fit: cover; z-index: -1;"
    autoplay muted loop playsinline preload="auto" poster="{poster_url}">
    <source src="{webm_url}" type="video/webm">
    <source src="{mp4_url}" type="video/mp4">
  </video>
  <div style="position: relative; z-index: 1; padding: 2rem; color: white; text-align: center; display: flex; flex-direction: column; justify-content: center; height: 100vh;">
    <h1 style="font-size: 3rem; margin-bottom: 1rem;">Your Landing Page Headline</h1>
    <p style="font-size: 1.2rem; margin-bottom: 2rem;">Replace with your content</p>
    <button style="background: #007cba; color: white; border: none; padding: 1rem 2rem; border-radius: 5px;">Call to Action</button>
  </div>
</div>"""

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        response = {
            "message": "Cinematic Video Optimizer API is running!",
            "status": "healthy"
        }
        self.wfile.write(json.dumps(response).encode())
        
    def do_POST(self):
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            # Parse JSON data
            data = json.loads(post_data.decode('utf-8'))
            
            # Extract video file (base64)
            video_file = data.get('videoFile', '')
            project_name = data.get('projectName', 'untitled')
            customer_email = data.get('customerEmail', 'anonymous')
            
            if not video_file:
                self.send_error(400, "No video file provided")
                return
                
            # Handle base64 encoded files
            if video_file.startswith("data:"):
                header, encoded = video_file.split(",", 1)
                video_content = base64.b64decode(encoded)
                
                # Create temporary file
                with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as temp_file:
                    temp_file.write(video_content)
                    temp_file_path = temp_file.name
                
                # Upload to Cloudinary
                upload_result = cloudinary.uploader.upload(
                    temp_file_path,
                    resource_type="video",
                    public_id=f"cinematic-{project_name.lower().replace(' ', '-')}",
                    overwrite=True,
                    eager=[
                        {"format": "mp4", "quality": "auto:eco", "width": 1280, "height": 720},
                        {"format": "webm", "quality": "auto:eco", "width": 1280, "height": 720}
                    ],
                    eager_async=False
                )
                
                # Clean up
                os.unlink(temp_file_path)
                
                # Extract URLs
                original_url = upload_result['secure_url']
                mp4_url = upload_result['eager'][0]['secure_url'] if upload_result['eager'] else original_url
                webm_url = upload_result['eager'][1]['secure_url'] if len(upload_result['eager']) > 1 else original_url
                
                # Generate poster
                poster_url = cloudinary.CloudinaryImage(upload_result['public_id']).build_url(
                    resource_type="image",
                    format="jpg",
                    transformation=[{"width": 1280, "height": 720, "crop": "scale"}]
                )
                
                embed_code = generate_embed_code(mp4_url, webm_url, poster_url)
                
                response_data = {
                    "success": True,
                    "message": "Video optimized successfully!",
                    "optimizedFiles": {
                        "mp4": {"url": mp4_url},
                        "webm": {"url": webm_url},
                        "poster": {"url": poster_url}
                    },
                    "embedCode": embed_code
                }
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps(response_data).encode())
                
        except Exception as e:
            self.send_error(500, f"Error processing video: {str(e)}")
            
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
