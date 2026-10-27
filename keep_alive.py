from fastapi import FastAPI
import uvicorn
import threading

app = FastAPI()

@app.get("/")
def home():
    return {"status": "Bot is active and running!"}

def run_server():
    uvicorn.run(app, host="0.0.0.0", port=8080)

def keep_alive():
    t = threading.Thread(target=run_server)
    t.daemon = True
    t.start()
