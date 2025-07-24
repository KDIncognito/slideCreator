from gpt import gptHandler, gptContext
from documentHandling import cleantext as ct
import json, base64

class handler:
    def __init__(self, text:str = None):
        self.original_text = text
        # self.conv_history += text
        self.is_safe = False
        self.slide_content = dict
        self.image_directory = "images_and_files/"
        self.gpt_handle = gptHandler()
    
    def _extract_llm_response_text(self, response):
        """Helper method to extract text content from LLM response objects"""
        try:
            # Debug: Print what we're working with
            print(f"DEBUG: Response type: {type(response)}")
            print(f"DEBUG: Response: {response}")
            
            # Try different ways to extract text content
            if hasattr(response, 'choices') and len(response.choices) > 0:
                if hasattr(response.choices[0], 'message'):
                    content = response.choices[0].message.content
                    print(f"DEBUG: Extracted from message.content: {content}")
                    return str(content) if content is not None else ""
                elif hasattr(response.choices[0], 'text'):
                    content = response.choices[0].text
                    print(f"DEBUG: Extracted from choices[0].text: {content}")
                    return str(content) if content is not None else ""
            
            if hasattr(response, 'content'):
                content = response.content
                print(f"DEBUG: Extracted from content: {content}")
                return str(content) if content is not None else ""
            
            if hasattr(response, 'text'):
                content = response.text
                print(f"DEBUG: Extracted from text: {content}")
                return str(content) if content is not None else ""
                
            if isinstance(response, str):
                print(f"DEBUG: Response is already string: {response}")
                return response
            
            # Last resort: convert to string
            result = str(response)
            print(f"DEBUG: Converted to string: {result}")
            return result
            
        except Exception as e:
            print(f"Error extracting LLM response: {e}")
            return str(response) if response is not None else ""

    def _IsSafeToUse(self):
        """Check to see if the given text is safe to use."""
        is_malicious = self.gpt_handle.llm_handler(system=gptContext.malicious.system,
        user=gptContext.malicious.user.format(text_content=self.original_text),)
        
        mal_text = self._extract_llm_response_text(is_malicious)
        
        # CRITICAL FIX: Ensure mal_text is always a string
        if mal_text is None:
            mal_text = ""
        elif not isinstance(mal_text, str):
            mal_text = str(mal_text)
        
        # Only proceed if we have actual text content
        if not mal_text.strip():
            self.is_safe = True
            return True
        
        # QUICK FIX: Skip clean_text since JSON is already clean
        try:
            mal = json.loads(mal_text)
        except json.JSONDecodeError:
            # If JSON parsing fails, try cleaning first
            cleaned_text = ct.clean_text(mal_text)
            mal = json.loads(cleaned_text)
        
        if mal.get('is_safe') is True:
            self.is_safe = True
            return True
        else:
            raise ValueError(f"The provided text is not safe to use. Please check the content and try again. {mal}")

    def _convert_content_to_slides(self):
        """Convert given text into content for slides."""
        slides = self.gpt_handle.llm_handler(system = gptContext.convertToSlides.system,
                user = gptContext.convertToSlides.user.format(text_content = self.original_text))
        
        slide_text = self._extract_llm_response_text(slides)
        
        # CRITICAL FIX: Ensure slide_text is always a string
        if slide_text is None:
            slide_text = ""
        elif not isinstance(slide_text, str):
            slide_text = str(slide_text)
        
        # Debug what we're about to process
        print(f"DEBUG _convert_content_to_slides: slide_text = '{slide_text}'")
        print(f"DEBUG _convert_content_to_slides: slide_text type = {type(slide_text)}")
        
        # Only proceed if we have actual text content
        if not slide_text.strip():
            print("WARNING: Empty response from slide generation LLM")
            self.slide_content = {"slides": []}
            return
        
        # QUICK FIX: Skip clean_text since JSON might already be clean
        try:
            self.slide_content = json.loads(slide_text)
        except json.JSONDecodeError:
            print("DEBUG: JSON parsing failed, trying with clean_text...")
            try:
                # If JSON parsing fails, try cleaning first
                slide_content = ct.clean_text(slide_text)
                print(f"DEBUG: After cleaning: '{slide_content}'")
                self.slide_content = json.loads(slide_content)
            except json.JSONDecodeError as e:
                print(f"ERROR: Still can't parse JSON after cleaning: {e}")
                print(f"Raw content: '{slide_text}'")
                # Fallback: create empty slides structure
                self.slide_content = {"slides": []}

    def _generate_image(self, image_prompt:str=None, filename:str=None):
        """
        Generates an image from a text input.
        """
        if not image_prompt or not filename:
            print(f"ERROR: Missing image_prompt ({image_prompt}) or filename ({filename})")
            return
            
        print(f"DEBUG: Generating image with prompt: {image_prompt[:100]}...")
        print(f"DEBUG: Saving as: {filename}")
        
        try:
            # Call the image generation API
            response = self.gpt_handle.llm_image_call(prompt=image_prompt)
            
            if response is None:
                print("ERROR: Image generation API returned None")
                return
                
            print(f"DEBUG: Image API response type: {type(response)}")
            
            # Access the Base64 data from the response
            if hasattr(response, 'data') and response.data and len(response.data) > 0:
                image_data = response.data[0]
                
                if hasattr(image_data, 'b64_json') and image_data.b64_json:
                    print("DEBUG: Found b64_json data, decoding...")
                    image_b64 = image_data.b64_json
                    
                    # Decode the Base64 string
                    image_bytes = base64.b64decode(image_b64)
                    
                    # Ensure directory exists
                    import os
                    if not os.path.exists(self.image_directory):
                        os.makedirs(self.image_directory)
                        print(f"DEBUG: Created directory {self.image_directory}")

                    # Save the image to a file
                    full_path = os.path.join(self.image_directory, f"{filename}.png")
                    with open(full_path, "wb") as f:
                        f.write(image_bytes)
                    print(f"✅ Image saved successfully as {full_path}")
                else:
                    print("ERROR: No b64_json data found in response")
                    print(f"DEBUG: Image data attributes: {dir(image_data)}")
            else:
                print("ERROR: No image data found in the response")
                print(f"DEBUG: Response attributes: {dir(response)}")

        except ImportError as e:
            print(f"ERROR: Missing required module: {e}")
        except (ValueError, ConnectionError, RuntimeError) as e:
            print(f"ERROR: Image generation failed: {e}")
        except Exception as e:
            print(f"ERROR: Unexpected error during image generation: {e}")
            import traceback
            traceback.print_exc()

    def _get_image_prompt(self):
        """
        For slides that need visuals, generate visuals and save them as image_placeholder_id
        """
        print("DEBUG: Starting _get_image_prompt...")
        _slides = self.slide_content.get('slides', None)
        print(f"DEBUG: Found {len(_slides) if _slides else 0} slides to process")
        
        if _slides:  # Add safety check
            images_processed = 0
            images_generated = 0
            
            for i, slide in enumerate(_slides):
                print(f"\nDEBUG: Processing slide {i+1}: {slide.get('title', 'No title')}")
                print(f"DEBUG: Slide keys: {list(slide.keys())}")
                
                imagery = slide.get("generated_visual_placeholder", None)
                print(f"DEBUG: Visual placeholder type: {type(imagery)}")
                print(f"DEBUG: Visual placeholder value: {imagery}")
                
                if imagery is None:
                    print("DEBUG: No visual placeholder (None)")
                    continue
                elif not isinstance(imagery, dict):
                    print(f"DEBUG: Visual placeholder is not a dict: {type(imagery)}")
                    continue
                
                need_image = imagery.get("need_image", None)
                print(f"DEBUG: need_image value: {need_image} (type: {type(need_image)})")
                
                if not need_image:
                    print("DEBUG: Image not needed for this slide")
                    continue
                
                images_processed += 1
                print(f"DEBUG: Processing image {images_processed}...")
                
                image_base_txt = imagery.get("source_text_for_visual", None)
                image_id = imagery.get("image_placeholder_id", "unknown_image")
                
                print(f"DEBUG: Processing image generation for ID: {image_id}")
                print(f"DEBUG: Source text: {image_base_txt}")
                
                if not image_base_txt:
                    print("WARNING: No source text for visual")
                    continue
                
                # First, get the image prompt from LLM (text response)
                print(f"DEBUG: Calling LLM for image prompt generation...")
                image_prompt_response = self.gpt_handle.llm_handler(
                    system=gptContext.generateImagePrompts.system,
                    user=gptContext.generateImagePrompts.user.format(image_base_txt)
                )
                
                # Extract the text response and parse it
                image_prompt_text = self._extract_llm_response_text(image_prompt_response)
                
                # CRITICAL FIX: Ensure image_prompt_text is always a string
                if image_prompt_text is None:
                    image_prompt_text = ""
                elif not isinstance(image_prompt_text, str):
                    image_prompt_text = str(image_prompt_text)
                
                # Only proceed if we have actual text content
                if not image_prompt_text.strip():
                    print("WARNING: Empty response from image prompt LLM")
                    continue
                
                print(f"DEBUG: Raw image prompt response: {image_prompt_text[:200]}...")
                
                # Parse the JSON response to get the actual image prompt
                try:
                    # Try to parse as JSON first
                    prompt_data = json.loads(image_prompt_text)
                    
                    # Extract the actual prompt from the JSON structure
                    if isinstance(prompt_data, dict):
                        # Look for common fields that contain the actual prompt
                        actual_prompt = (
                            prompt_data.get('image_prompt') or 
                            prompt_data.get('prompt') or 
                            prompt_data.get('description') or
                            image_prompt_text
                        )
                    elif isinstance(prompt_data, list) and len(prompt_data) > 0:
                        # If it's a list, take the first item's prompt
                        first_item = prompt_data[0]
                        if isinstance(first_item, dict):
                            actual_prompt = (
                                first_item.get('image_prompt') or 
                                first_item.get('prompt') or 
                                first_item.get('description') or
                                str(first_item)
                            )
                        else:
                            actual_prompt = str(first_item)
                    else:
                        actual_prompt = str(prompt_data)
                        
                except json.JSONDecodeError:
                    print("DEBUG: Not JSON, using raw text as prompt")
                    # If not JSON, clean and use as-is
                    actual_prompt = ct.clean_text(image_prompt_text)
                
                print(f"DEBUG: Final image prompt: {actual_prompt}")
                
                # Now generate the actual image
                print(f"DEBUG: Calling _generate_image...")
                self._generate_image(actual_prompt, filename=image_id)
                images_generated += 1
                
            print(f"\nDEBUG: Image processing summary:")
            print(f"  - Slides processed: {len(_slides)}")
            print(f"  - Images requested: {images_processed}")
            print(f"  - Images generated: {images_generated}")
        else:
            print("DEBUG: No slides found to process for images")

    def get_slide_content(self):
        """
        Execute all the steps to convert text to slides and generate images.
        """
        if self._IsSafeToUse():
            self._convert_content_to_slides()
            self._get_image_prompt()
        return self.slide_content