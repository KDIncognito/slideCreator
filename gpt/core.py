from openai import OpenAI
from dotenv import load_dotenv
import os, base64, requests

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
        )
        
        image_bytes = base64.b64decode(image_response.data[0].b64_json)
        with open("images/output.png", "wb") as f:
            f.write(image_bytes)
    
    def llm_handler(self, **kwargs):
        """
        Handle the LLM call based on the provided keyword arguments.
        This method dynamically constructs the system and user messages based on the class attributes.
        """
        if len(kwargs) == 0:
            raise ValueError("No parameters provided for llm_handler.")
        
        system = kwargs.get('system', None)
        user = kwargs.get('user', None)

        if isinstance(user, dict):
            user_message = "\n".join([f"{key}= {value}" for key, value in user.items()])
        else:
            user_message = user

        if isinstance(system, dict):
            system_message = "\n".join([f"{key}= {value}" for key, value in system.items()])
        else:
            system_message = system

        return self._llm_call(system_message, user_message)