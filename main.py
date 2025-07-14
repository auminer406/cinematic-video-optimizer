# Cinematic Landing Page Video Optimizer API
# Built with FastAPI for Vercel deployment

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import cloudinary
import cloudinary.uploader
import cloudinary.api
import os
import base64
import tempfile
from typing import Dict, Any
import json

app = FastAPI(title="Cinematic Video Optimizer", version="1.0.0")

# CORS middleware to allow requests from your frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with your actual domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure Cloudinary (you'll set these as environment variables in Vercel)
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME", "dg35cu9qf"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET")
)

def generate_embed_code(mp4_url: str, webm_url: str, poster_url: str) -> str:
    """Generate optimized HTML embed code for landing page backgrounds"""
    
    embed_code = f"""<!-- Cinematic Landing Page Video - Optimized by CinematicLandingPage.com -->
<div class="cinematic-hero" style="position: relative; width: 100%; height: 100vh; overflow: hidden;">
  <video 
    style="
      position: absolute;
      top: 50%;
      left: 50%;
      min-width: 100%;
      min-height: 100%;
      width: auto;
      height: auto;
      transform: translate(-50%, -50%);
      object-fit: cover;
      z-index: -1;
    "
    autoplay 
    muted 
    loop 
    playsinline 
    preload="auto"
    poster="{poster_url}">
    <source src="{webm_url}" type="video/webm">
    <source src="{mp4_url}" type="video/mp4">
    Your browser does not support the video tag.
  </video>
  
  <!-- Your content goes here -->
  <div style="position: relative; z-index: 1; padding: 2rem; color: white; text-align: center; display: flex; flex-direction: column; justify-content: center; height: 100vh;">
    <h1 style="font-size: 3rem; margin-bottom: 1rem;">Your Landing Page Headline</h1>
    <p style="font-size: 1.2rem; margin-bottom: 2rem;">Replace this with your actual content</p>
    <button style="background: #007cba; color: white; border: none; padding: 1rem 2rem; border-radius: 5px; font-size: 1.1rem; cursor: pointer;">Call to Action</button>
  </div>
</div>

<style>
/* Responsive adjustments */
@media (max-width: 768px) {{
  .cinematic-hero {{
    height: 60vh; /* Shorter on mobile to save bandwidth */
  }}
  .cinematic-hero h1 {{
    font-size: 2rem;
  }}
}}

/* Ensure video doesn't interfere with content */
.cinematic-hero video {{
  pointer-events: none;
}}
</style>

<!-- Performance: Video loads immediately for hero sections -->"""
    
    return embed_code

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "Cinematic Video Optimizer API is running!", "status": "healthy"}

@app.post("/optimize-video")
async def optimize_video(
    videoFile: UploadFile = File(...),
    projectName: str = Form(...),
    customerEmail: str = Form(...)
) -> JSONResponse:
    """
    Optimize uploaded video for landing page use
    Returns optimized video URLs and embed code
    """
    
    try:
        # Validate file type
        if not videoFile.content_type.startswith('video/'):
            raise HTTPException(status_code=400, detail="File must be a video")
        
        # Read the uploaded file
        video_content = await videoFile.read()
        
        # Create a temporary file for upload
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as temp_file:
            temp_file.write(video_content)
            temp_file_path = temp_file.name
        
        try:
            # Upload to Cloudinary with optimizations
            upload_result = cloudinary.uploader.upload(
                temp_file_path,
                resource_type="video",
                public_id=f"cinematic-{projectName.lower().replace(' ', '-')}-{hash(customerEmail) % 10000}",
                overwrite=True,
                eager=[
                    {
                        "format": "mp4",
                        "quality": "auto:eco",
                        "width": 1280,
                        "height": 720,
                        "crop": "scale",
                        "fetch_format": "auto",
                        "flags": "streaming_optimization"
                    },
                    {
                        "format": "webm",
                        "quality": "auto:eco", 
                        "width": 1280,
                        "height": 720,
                        "crop": "scale",
                        "fetch_format": "auto",
                        "flags": "streaming_optimization"
                    }
                ],
                eager_async=False,  # Wait for transformations to complete
            )
            
            # Extract URLs
            original_url = upload_result['secure_url']
            
            # Get optimized format URLs
            mp4_url = upload_result['eager'][0]['secure_url'] if upload_result['eager'] else original_url
            webm_url = upload_result['eager'][1]['secure_url'] if len(upload_result['eager']) > 1 else original_url
            
            # Generate poster image URL (first frame)
            poster_url = cloudinary.CloudinaryImage(upload_result['public_id']).build_url(
                resource_type="image",
                format="jpg",
                transformation=[
                    {"quality": "auto:eco"},
                    {"width": 1280, "height": 720, "crop": "scale"},
                    {"start_offset": "1.0"}  # Take frame at 1 second
                ]
            )
            
            # Generate embed code
            embed_code = generate_embed_code(mp4_url, webm_url, poster_url)
            
            # Prepare response
            response_data = {
                "success": True,
                "message": "Video optimized successfully!",
                "optimizedFiles": {
                    "mp4": {
                        "url": mp4_url,
                        "format": "MP4 (H.264)",
                        "description": "Best compatibility across all devices"
                    },
                    "webm": {
                        "url": webm_url,
                        "format": "WebM (VP9)",
                        "description": "Smaller file size for modern browsers"
                    },
                    "poster": {
                        "url": poster_url,
                        "format": "JPG",
                        "description": "Preview image for instant loading"
                    }
                },
                "embedCode": embed_code,
                "instructions": {
                    "step1": "Copy the embed code below",
                    "step2": "Paste it into your landing page HTML",
                    "step3": "Replace the placeholder content with your actual content",
                    "step4": "Publish and enjoy your professional video background!"
                },
                "technicalSpecs": {
                    "resolution": "1280x720 (720p HD)",
                    "formats": ["MP4 (broad compatibility)", "WebM (smaller size)"],
                    "optimization": "Auto-quality compression",
                    "posterImage": "Auto-generated from video frame",
                    "mobileOptimized": True,
                    "loadingStrategy": "Immediate (optimized for hero sections)"
                }
            }
            
            return JSONResponse(content=response_data)
            
        finally:
            # Clean up temporary file
            os.unlink(temp_file_path)
            
    except Exception as e:
        # Log the error (in production, use proper logging)
        print(f"Error processing video: {str(e)}")
        
        # Return error response
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process video: {str(e)}"
        )

@app.post("/optimize-video-url")
async def optimize_video_from_url(
    video_data: Dict[str, Any]
) -> JSONResponse:
    """
    Alternative endpoint for base64 encoded videos (from your existing frontend)
    """
    
    try:
        video_file = video_data.get("videoFile")
        project_name = video_data.get("projectName", "untitled")
        customer_email = video_data.get("customerEmail", "anonymous")
        
        if not video_file:
            raise HTTPException(status_code=400, detail="No video file provided")
        
        # Handle base64 encoded files
        if video_file.startswith("data:"):
            # Extract base64 data
            header, encoded = video_file.split(",", 1)
            video_content = base64.b64decode(encoded)
            
            # Create temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as temp_file:
                temp_file.write(video_content)
                temp_file_path = temp_file.name
        else:
            # Assume it's a URL
            temp_file_path = video_file
        
        # Same upload process as above
        upload_result = cloudinary.uploader.upload(
            temp_file_path,
            resource_type="video",
            public_id=f"cinematic-{project_name.lower().replace(' ', '-')}-{hash(customer_email) % 10000}",
            overwrite=True,
            eager=[
                {
                    "format": "mp4",
                    "quality": "auto:eco",
                    "width": 1280,
                    "height": 720,
                    "crop": "scale"
                },
                {
                    "format": "webm",
                    "quality": "auto:eco",
                    "width": 1280,
                    "height": 720,
                    "crop": "scale"
                }
            ],
            eager_async=False
        )
        
        # Process results same as above...
        original_url = upload_result['secure_url']
        mp4_url = upload_result['eager'][0]['secure_url'] if upload_result['eager'] else original_url
        webm_url = upload_result['eager'][1]['secure_url'] if len(upload_result['eager']) > 1 else original_url
        
        poster_url = cloudinary.CloudinaryImage(upload_result['public_id']).build_url(
            resource_type="image",
            format="jpg",
            transformation=[
                {"quality": "auto:eco"},
                {"width": 1280, "height": 720, "crop": "scale"},
                {"start_offset": "1.0"}
            ]
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
        
        return JSONResponse(content=response_data)
        
        # Clean up if we created a temp file
        if video_file.startswith("data:") and os.path.exists(temp_file_path):
            os.unlink(temp_file_path)
            
    except Exception as e:
        print(f"Error processing video from URL: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to process video: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)