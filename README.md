# 🚀 Latency-Optimized AI Agent Backend

A high-performance microservice architecture designed for **Voice Agents** and **Real-time Support Systems**. 
Built with **FastAPI**, **Redis**, **PostgreSQL**, and **Groq (LPU Inference)**.

## 🎯 The Problem
In voice AI applications, latency is the critical bottleneck. Standard LLM API calls can take 500ms+, which creates awkward pauses in conversation. 
This project solves this by implementing a **multi-layer caching strategy**.

## 🏗 Architecture

The system is orchestrated via **Docker Compose** and consists of 3 services:

1.  **FastAPI Service (Async):** Handles requests non-blocking.
2.  **Redis (Cache Layer):** Stores frequent queries in RAM for **<5ms** response time.
3.  **PostgreSQL (Persistence Layer):** Asynchronously logs all interactions for MLOps/Analytics.
4.  **Groq (Inference):** Uses LPU hardware for ultra-fast token generation when cache misses occur.

## 🛠 Tech Stack

*   **Language:** Python 3.9+
*   **Framework:** FastAPI (AsyncIO)
*   **Database:** PostgreSQL (via `asyncpg`)
*   **Cache:** Redis
*   **LLM:** Llama-3-70b via Groq API
*   **DevOps:** Docker & Docker Compose

## 🚀 How to Run

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/YOUR_USERNAME/vandri-ai-agent.git
    cd vandri-ai-agent
    ```

2.  **Set up Environment Variables:**
    Create a `.env` file in the root directory and add your Groq API Key:
    ```text
    GROQ_API_KEY=gsk_your_key_here
    ```

3.  **Run with Docker Compose:**
    ```bash
    docker-compose up --build
    ```

4.  **Test the API:**
    Open your browser at `http://localhost:8000/docs`.

## 📊 Performance Demo

*   **First Request (Cache Miss):** ~500ms (Calls LLM)
*   **Second Request (Cache Hit):** **~3ms** (Served from Redis)

## 👨‍💻 Author
**Egor Volokitin**  
*Aspiring AI Engineer focused on scalable ML systems.*