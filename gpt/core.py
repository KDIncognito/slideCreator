from openai import OpenAI
from dotenv import load_dotenv
import os

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
            ,response_format={"type": "json_object"}
        )
        # return completion.choices[0].message.content.strip()
        return completion.choices[0].message.content

    def llm_image_call(self, prompt):
        # Call the OpenAI API to generate an image based on the prompt
        try:
            image_response = self.client.images.generate(
                model="dall-e-3",  # FIX: Use correct DALL-E model
                prompt=prompt,
                n=1,
                size="1024x1024",
                response_format="b64_json"  # FIX: Use correct parameter name
            )
            
            # Return the full response object, not decoded bytes
            # This allows handler.py to access both data and b64_json
            return image_response
            
        except (ValueError, ConnectionError, RuntimeError) as e:
            print(f"Error generating image: {e}")
            return None

    
    def llm_handler(self, system, user, request_type="text"):
        """
        Handle the LLM call based on the provided keyword arguments.
        This method dynamically constructs the system and user messages based on the class attributes.
        """
        # "image_url": {"url": f"data:image/jpeg;base64,{image_data}"}
        if request_type == "image":
            return self.llm_image_call(user)
        
        return self._llm_call(system, user)
