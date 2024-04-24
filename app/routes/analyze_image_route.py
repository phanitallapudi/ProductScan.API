from fastapi import APIRouter, Query, HTTPException, Depends, Request, status, File, UploadFile
from fastapi.responses import JSONResponse
from typing import List

from app.classes.analyze_image_management import ImageInformation
from app.classes.analyze_image_management import get_image_informations, translate_text
from app.classes.login import get_current_user, authorize_user, authorize_both_user, oauth2_scheme, User
from utils.file_utils import save_file_async

import os

router = APIRouter()

@router.post("/analyze-image/", response_model=ImageInformation, dependencies=[Depends(authorize_user)])
async def analyze_image(files: List[UploadFile] = File(...), current_user: User = Depends(get_current_user), token: str = Depends(oauth2_scheme)):
    # Save the file to a temporary location
    username = "test"  # Change the functionality later
    storage_directory = f"data/{username}_files"
    os.makedirs(storage_directory, exist_ok=True)

    en_results = []
    ar_results = []
    for file in files:
        await save_file_async(file, storage_directory)
        file_path = f"{storage_directory}/{file.filename}"
        try:
            result = get_image_informations(file_path)
        except Exception as e:
            en_results.append({f"message" : "Cannot able to process the request, please try again.."})
        en_results.append({f"{file.filename}" : result})
    
    for item in en_results:
        translated_item = {}
        for key, value in item.items():
            translated_value = {}
            for field, text in value.items():
                if isinstance(text, list):
                    translated_text = [translate_text(t) for t in text]
                    translated_value[field] = translated_text
                else:
                    translated_value[field] = translate_text(text)
            translated_item[key] = translated_value
        ar_results.append(translated_item)
    
    response = {
        "en" : en_results,
        "ar" : ar_results
    }

    return JSONResponse(content=response, status_code=200)