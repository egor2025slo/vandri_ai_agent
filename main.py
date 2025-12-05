import os
import logging
import datetime
import traceback
from typing import Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from databases import Database
import redis
from groq import Groq

# --- LOGGING CONFIGURATION ---
# In production, logs are critical for observability.
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- ENVIRONMENT VARIABLES ---
# We use os.getenv to keep secrets out of the codebase.
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://vandri_user:secretpassword@db:5432/vandri_db")
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# --- INITIALIZATION ---
app = FastAPI(
    title="Vandri AI Agent Backend",
    description="High-performance microservice with Redis caching and Async DB logging.",
    version="1.0.0"
)

database = Database(DATABASE_URL)

# Initialize Redis with error handling
try:
    redis_client = redis.Redis.from_url(REDIS_URL, decode_responses=True)
    logger.info("Connected to Redis successfully.")
except Exception as e:
    logger.error(f"Failed to connect to Redis: {e}")
    redis_client = None

# Initialize Groq (LLM Provider)
if GROQ_API_KEY:
    groq_client = Groq(api_key=GROQ_API_KEY)
    logger.info("Groq Client initialized.")
else:
    logger.warning("GROQ_API_KEY not found. LLM features will fail.")
    groq_client = None


# --- DATA MODELS (Pydantic) ---
class UserQuery(BaseModel):
    user_id: int
    text: str

class AgentResponse(BaseModel):
    response: str
    source: str
    latency_seconds: float


# --- LIFECYCLE EVENTS ---
@app.on_event("startup")
async def startup():
    """
    Runs on application startup.
    Connects to the database and ensures the logs table exists.
    """
    try:
        await database.connect()
        logger.info("Connected to PostgreSQL.")
        
        # Create table for analytics if it doesn't exist
        query = """
            CREATE TABLE IF NOT EXISTS interactions (
                id SERIAL PRIMARY KEY,
                user_id INTEGER,
                input_text TEXT,
                ai_response TEXT,
                source VARCHAR(20),
                timestamp TIMESTAMP DEFAULT NOW()
            )
        """
        await database.execute(query)
        logger.info("Database schema initialized.")
    except Exception as e:
        logger.critical(f"Database connection failed: {e}")

@app.on_event("shutdown")
async def shutdown():
    """Closes database connection on shutdown."""
    await database.disconnect()
    logger.info("Database connection closed.")


# --- ENDPOINTS ---

@app.post("/chat", response_model=AgentResponse)
async def chat_endpoint(query: UserQuery):
    """
    Main conversational endpoint.
    Logic:
    1. Check Redis Cache (for < 5ms latency).
    2. If miss, call Groq LLM (LPU inference).
    3. Cache the result asynchronously.
    4. Log the interaction to Postgres for analytics.
    """
    start_time = datetime.datetime.now()
    source = "unknown"
    response_text = ""

    try:
        # 1. CACHE LAYER (Redis)
        if redis_client:
            cached_response = redis_client.get(query.text)
            if cached_response:
                source = "cache (Redis)"
                response_text = cached_response
                logger.info(f"Cache hit for query: {query.text[:20]}...")

        # 2. INFERENCE LAYER (LLM)
        if not response_text:
            if not groq_client:
                raise HTTPException(status_code=500, detail="LLM service not configured.")
            
            source = "llm (Groq)"
            logger.info("Cache miss. Calling LLM...")
            
            chat_completion = groq_client.chat.completions.create(
                messages=[
                    {
                        "role": "system", 
                        "content": "You are a helpful and concise AI assistant for Vandri.ai."
                    },
                    {
                        "role": "user", 
                        "content": query.text
                    }
                ],
                # Using the latest efficient model
                model="llama-3.3-70b-versatile",
            )
            response_text = chat_completion.choices[0].message.content

            # Write to cache (TTL: 1 hour)
            if redis_client:
                redis_client.setex(query.text, 3600, response_text)

        # 3. PERSISTENCE LAYER (Postgres)
        # We log everything for future fine-tuning and analysis
        await database.execute(
            "INSERT INTO interactions(user_id, input_text, ai_response, source) VALUES (:uid, :inp, :resp, :src)",
            values={
                "uid": query.user_id, 
                "inp": query.text, 
                "resp": response_text, 
                "src": source
            }
        )

        process_time = (datetime.datetime.now() - start_time).total_seconds()
        
        return {
            "response": response_text,
            "source": source,
            "latency_seconds": process_time
        }

    except Exception as e:
        logger.error(f"Error processing request: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/analytics")
async def get_analytics():
    """Returns the last 10 interactions from the database."""
    try:
        return await database.fetch_all("SELECT * FROM interactions ORDER BY id DESC LIMIT 10")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))