from sched import scheduler
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# ----------------------------
# CORS Middleware (updated)
# ----------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ⚠️ only for testing!
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----------------------------
# Include Routers
# ----------------------------
# app.include_router(auth_router.router)





# ----------------------------
# Root
# ----------------------------
@app.get("/")
async def root():
    return {"message": "Hello, simba_cement is running!"}

