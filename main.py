from fastapi import FastAPI, HTTPException, File, UploadFile
from fastapi.responses import JSONResponse, RedirectResponse
from pydantic import BaseModel
from typing import List
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage
from langchain.chains import TransformChain
from langchain_core.runnables import chain
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.pydantic_v1 import Field
from langchain_openai import ChatOpenAI
from pathlib import Path
import os
import base64
import aiofiles
import os

load_dotenv()

os.environ["AZURE_OPENAI_API_KEY"] = os.getenv('AZURE_OPENAI_API_KEY')
os.environ["AZURE_OPENAI_ENDPOINT"] = os.getenv('AZURE_OPENAI_ENDPOINT')
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")

class ImageInformation(BaseModel):
    """Information about an image."""
    image_description: str = Field(description="a short description of the image")
    calories: str = Field(description="total calories in the image")
    fats: str = Field(description="total fats in the image")
    sodium: str = Field(description="total sodium in the image")
    added_sugar: str = Field(description="total added sugars in the image")
    protein: str = Field(description="total protein in the image")
    main_objects: List[str] = Field(description="list of the main objects on the picture")

app = FastAPI()

async def save_file_async(file, storage_directory):
    """
    Save an uploaded file asynchronously.

    Parameters:
    - file: UploadFile - The uploaded file.
    - storage_directory: str - The directory where the file should be saved.
    """
    # Remove any previous files in the directory
    for filename in os.listdir(storage_directory):
        file_path = os.path.join(storage_directory, filename)
        if os.path.isfile(file_path):
            os.remove(file_path)

    # Save the current file
    file_path = os.path.join(storage_directory, file.filename)

    async with aiofiles.open(file_path, 'wb') as out_file:
        content = await file.read()
        await out_file.write(content)

def load_image(inputs: dict) -> dict:
    """Load image from file and encode it as base64."""
    image_path = inputs["image_path"]
  
    def encode_image(image_path):
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    image_base64 = encode_image(image_path)
    return {"image": image_base64}

load_image_chain = TransformChain(
    input_variables=["image_path"],
    output_variables=["image"],
    transform=load_image
)

parser = JsonOutputParser(pydantic_object=ImageInformation)

@chain
def image_model(inputs: dict) -> str | List[str] | dict:
    """Invoke model with image and prompt."""
    model = ChatOpenAI(temperature=0.5, model="gpt-4-vision-preview", max_tokens=1024)
    msg = model.invoke(
                [HumanMessage(
                content=[
                {"type": "text", "text": inputs["prompt"]},
                {"type": "text", "text": parser.get_format_instructions()},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{inputs['image']}"}},
                ])]
                )
    return msg.content

def get_image_informations(image_path: str) -> dict:
   vision_prompt = """
   Given the image, provide the following information:
   - A count of how many people are in the image
   - A list of the main objects present in the image
   - A description of the image
   """
   vision_chain = load_image_chain | image_model | parser
   return vision_chain.invoke({'image_path': f'{image_path}', 
                               'prompt': vision_prompt})

class ImagePath(BaseModel):
    image_path: str

@app.post("/analyze-image/", response_model=ImageInformation)
async def analyze_image(files: List[UploadFile] = File(...)):
    # Save the file to a temporary location
    username = "test"  # Change the functionality later
    storage_directory = f"data/{username}_files"
    os.makedirs(storage_directory, exist_ok=True)

    results = []
    for file in files:
        await save_file_async(file, storage_directory)
        file_path = f"{storage_directory}/{file.filename}"
        result = get_image_informations(file_path)
        results.append({f"{file.filename}" : result})

    return JSONResponse(content=results, status_code=200)

@app.get("/")
async def root():
    return RedirectResponse(url="/docs")