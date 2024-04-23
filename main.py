
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from app.routes.login_route import router as login_router
from app.routes.analyze_image_route import router as analyze_image_router


app = FastAPI(
    title="ProductScan.API",
    swagger_ui_parameters={"syntaxHighlight": False}
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(login_router, tags=["Authenticate"])
app.include_router(analyze_image_router, prefix="/image", tags=["Analyze Images"])

@app.get("/")
async def root():
    return RedirectResponse(url="/docs")