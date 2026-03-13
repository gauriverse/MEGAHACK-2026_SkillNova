from fastapi              import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.routes       import burnout

app = FastAPI(
    title       = "SkillNova API",
    description = "AI-powered student burnout prediction and productivity tracking",
    version     = "1.0.0",
)

# CORS — update origins for production
app.add_middleware(
    CORSMiddleware,
    allow_origins     = ["http://localhost:3000", "http://localhost:5173"],
    allow_credentials = True,
    allow_methods     = ["*"],
    allow_headers     = ["*"],
)

# Routers
app.include_router(burnout.router)

@app.get("/")
async def root():
    return {"message": "SkillNova API is running 🚀"}