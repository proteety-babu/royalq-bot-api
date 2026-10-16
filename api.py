from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import asyncio
import bot_engine

app = FastAPI(title="Royal Q Clone API", version="1.1")

# CORS সেটআপ (যাতে ফ্লাটার অ্যাপ কানেক্ট হতে পারে)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # সব ওয়েবসাইট বা অ্যাপকে অনুমতি দেওয়া হলো
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

active_bots = {}

class BotSettings(BaseModel):
    symbol: str = "BTC/USDT"
    first_buy_amount: float = 15.0
    take_profit_pct: float = 1.5
    drop_to_buy_pct: float = 2.0
    max_margin_calls: int = 4

class StopRequest(BaseModel):
    symbol: str = "BTC/USDT"

@app.get("/")
def home():
    return {"message": "✅ Royal Q API Server is Running!"}

@app.get("/bot-status")
def get_bot_status():
    return {"active_bots": active_bots}

@app.post("/start-bot")
async def start_bot(settings: BotSettings):
    symbol = settings.symbol
    
    if symbol in active_bots and active_bots[symbol]["is_running"]:
        return {"message": f"⚠️ {symbol} এর জন্য বট আগে থেকেই চলছে!"}
    
    active_bots[symbol] = {
        "is_running": True,
        "settings": {
            "symbol": symbol,
            "first_buy_amount": settings.first_buy_amount,
            "take_profit_pct": settings.take_profit_pct,
            "drop_to_buy_pct": settings.drop_to_buy_pct,
            "max_margin_calls": settings.max_margin_calls
        }
    }
    
    asyncio.create_task(bot_engine.start_trading_engine(active_bots[symbol]))
    
    return {
        "message": f"🚀 {symbol} এর জন্য নতুন বট চালু করা হয়েছে!",
        "configured_settings": active_bots[symbol]["settings"]
    }

@app.post("/stop-bot")
def stop_bot(request: StopRequest):
    symbol = request.symbol
    
    if symbol not in active_bots or not active_bots[symbol]["is_running"]:
        return {"message": f"⚠️ {symbol} এর জন্য কোনো বট চলছে না!"}
    
    active_bots[symbol]["is_running"] = False 
    return {"message": f"🛑 {symbol} এর বট থামানোর সিগন্যাল পাঠানো হয়েছে।"}