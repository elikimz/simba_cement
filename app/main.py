from sched import scheduler
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import users, settings,categories,products,cart,order,address

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
app.include_router(users.router)
app.include_router(settings.router)
app.include_router(categories.router)
app.include_router(products.router)
app.include_router(cart.router)
app.include_router(order.router)
app.include_router(address.router)




# ----------------------------
# Root
# ----------------------------
@app.get("/")
async def root():
    return {"message": "Hello, simba_cement is running!"}

