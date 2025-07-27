import base64
from .core import gptHandler
from .supportContext import gptContext
from typing import Dict, Any

class ImageAnalyzer:
    def __init__(self):
        self.gpt_handler = gptHandler()
        self.analysis_prompt = gptContext.imageAnalysis.user
    
    def encode_image_to_base64(self, image_path: str) -> str:
        """Convert image to base64 string for GPT vision API."""
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    
    def analyze_image(self, image_path: str) -> Dict[str, Any]:
        """Analyze a single image and extract comprehensive content."""
        try:
            # Encode image for GPT vision
            base64_image = self.encode_image_to_base64(image_path)
            
            # Create message with image for GPT-4 vision
            messages = [
                {"role": "system", "content": gptContext.imageAnalysis.system},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": gptContext.imageAnalysis.user},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ]
            
            # Use gptHandler with vision capability
            analysis = self.gpt_handler.llm_handler(
                system="", 
                user="", 
                request_type="vision", 
                messages=messages
            )
            
            return {
                "image_path": image_path,
                "analysis": analysis,
                "status": "success"
            }
            
        except Exception as e:
            return {
                "image_path": image_path,
                "analysis": None,
                "status": "error",
                "error": str(e)
            }
