from documentHandling import ReadDoc, pptHandling
from gpt import gptHandler
gp = gptHandler()

kwargs = {"system": "You are a helpful assistant that creates PowerPoint presentations.",
    "user": {'breakdown':'this document was brokendown','original':'this document is the original source.'}}

gp.llm_handler(**kwargs)
# Function to read contents of the document file.

# Breakdown the given document into individual concepts

# Establish the flow between the concepts

# Convert the concepts into a slide format

# Create image prompts for for the slides that may require images

# Put it all together.

# Save the file as a pptx file.

# Upload a copy to AWS