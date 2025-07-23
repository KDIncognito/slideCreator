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
    
    def _IsSafeToUse(self):
        """
        Check to see if the given text is safe to use.
        """
        is_malicious = self.gpt_handle.llm_handler(system=gptContext.malicious.system,
        user=gptContext.malicious.user.format(text_content=self.original_text),)
        mal = ct.clean_text(is_malicious)
        mal = json.loads(mal)
        if mal.get('is_safe') is True:
            self.is_safe = True
        else:
            raise ValueError(f"The provided text is not safe to use. Please check the content and try again. {mal}")
    
    def _convert_content_to_slides(self):
        """ 
        Convert given text into content for slides.
        """
        slides = self.gpt_handle.llm_handler(system = gptContext.convertToSlides.system,
                   user = gptContext.convertToSlides.user.format(text_content = self.original_text))
        slide_content = ct.clean_text(slides)
        self.slide_content = json.loads(slide_content)
    
    def _generate_image(self, image_prompt:str=None, filename:str=None):
        """
        Generates an image from a text input.
        """
        # gp.llm_image_call(prompt = image_prompt)
        try:
            response = self.gpt_handle.llm_image_call(prompt = image_prompt)

        # Access the Base64 data from the response
            if response.data and response.data[0].b64_json:
                image_b64 = response.data[0].b64_json
                
                # Decode the Base64 string
                image_bytes = base64.b64decode(image_b64)

                # Save the image to a file
                with open(self.image_directory+filename+'.png', "wb") as f:
                    f.write(image_bytes)
                print(f"Image saved successfully as {filename}")
            else:
                print("No image data found in the response.")

        except Exception as e:
            print(f"An error occurred: {e}")


    def _get_image_prompt(self):
        """
        For slides that need visuals, generate visuals and save them as image_placeholder_id
        """
        _slides = self.slide_content.get('slides', None)
        for slide in _slides:
            imagery = slide.get("generated_visual_placeholder", None)
            if imagery.get("need_image", None):
                image_base_txt = imagery.get("source_text_for_visual", None)
                image_prompt = self.gpt_handle.llm_handler(system = gptContext.generateImagePrompts.system,
                                       user = gptContext.generateImagePrompts.user.format(image_base_txt))
                image_prompt = ct.clean_text(image_prompt)
                self._generate_image(image_prompt, filename=imagery.get("image_placeholder_id"))


    def get_slide_content(self):
        """
        Execute all the steps to convert text to slides and generate images.
        """
        if self._IsSafeToUse():
            self._convert_content_to_slides()
            self._get_image_prompt()
        return self.slide_content