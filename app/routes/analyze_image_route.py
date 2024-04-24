from fastapi import APIRouter, Query, HTTPException, Depends, Request, status, File, UploadFile, Response
from fastapi.responses import JSONResponse
from typing import List

from app.classes.analyze_image_management import ImageInformation
from app.classes.analyze_image_management import get_image_informations, translate_text
from app.classes.login import get_current_user, authorize_user, authorize_both_user, oauth2_scheme, User
from utils.file_utils import save_file_async

import os
import csv

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
            en_results.append({file.filename: result})
        except Exception as e:
            en_results.append({file.filename: {"error_message": "Cannot able to process the request, please try again.."}})
    
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

    product_data = []
    for language in response:
        for product_info in response[language]:
            if "error_message" in product_info:
                product_data.append([product_info["error_message"]])
            for _, product_details in product_info.items():
                product_data.append([
                    product_details.get('product_name', ''),
                    product_details.get('company_name', ''),
                    product_details.get('quantity', ''),
                    product_details.get('product_description', ''),
                    product_details.get('product_price', ''),
                    ', '.join(product_details.get('ingredients', [])),
                    ', '.join(product_details.get('remarks', []))
                ])

    # Writing to CSV
    with open('products.csv', 'w', newline='', encoding='utf-8') as csvfile:
        csv_writer = csv.writer(csvfile)
        csv_writer.writerow(['Product Name', 'Company Name', 'Quantity', 'Description', 'Price', 'Ingredients', 'Remarks'])
        csv_writer.writerows(product_data)

    return JSONResponse(content=response, status_code=200)


@router.get("/get-file/")
# async def get_file(file_path: str = Query(..., title="Query", description="Enter the question")):
async def get_file(current_user: User = Depends(get_current_user)):
    file_path = "products.csv"

    # Check if the file exists
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")

    # Read the file content
    with open(file_path, "rb") as file:
        file_content = file.read()

    # Return the file content as a blob with appropriate headers
    return Response(content=file_content, media_type="application/octet-stream")