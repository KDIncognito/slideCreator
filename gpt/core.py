from openai import OpenAI
from dotenv import load_dotenv
import os, base64

load_dotenv()


class gptHandler:
    def __init__(self):
        self.apiKey = os.getenv("gpt_key")
        self.client = OpenAI(api_key=self.apiKey)

    def _llm_call(self, system, user):
        # Dynamically import the sub class from GPTContext using the theme parameter
        completion = self.client.chat.completions.create(
            model="gpt-4o-mini",
            store=True,
            messages=[  
                {"role": "system", "content": system},
                {"role": "user", "content": user}
            ]  
        )
        
        return completion.choices[0].message.content.strip()

    def llm_image_call(self, prompt):
        # Call the OpenAI API to generate an image based on the prompt

        image_response = self.client.images.generate(
            model="gpt-image-1",
            prompt=prompt,
            n=1,
            size="1024x1024",
            output_format="png"
        )
        
        return base64.b64decode(image_response.data[0].b64_json)

    
    def llm_handler(self, system, user):
        """
        Handle the LLM call based on the provided keyword arguments.
        This method dynamically constructs the system and user messages based on the class attributes.
        """
        # "image_url": {"url": f"data:image/jpeg;base64,{image_data}"}
        return self._llm_call(system, user)