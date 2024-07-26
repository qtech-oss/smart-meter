from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from Adafruit_IO import Client, Feed, RequestError
import os
import requests
from dotenv import load_dotenv
import uuid


load_dotenv()

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["localhost", "localhost:3000", "localhost:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

#Replace these with values in the env file
ADAFRUIT_IO_USERNAME = os.environ.get('ADAFRUIT_IO_USERNAME')
ADAFRUIT_IO_KEY = os.environ.get('ADAFRUIT_IO_KEY')
PAYMENT_SECRET_KEY = os.environ.get('PAYMENT_SECRET_KEY')
ROOT_URL = os.environ.get('ROOT_URL')

@app.get("/payment_success")
def payment_success():
    return {"status": "Thanks for Paying"}

# Create an instance of the REST client.
@app.get("/create_user")
def read_root(username: str):
    aio = Client(ADAFRUIT_IO_USERNAME, ADAFRUIT_IO_KEY)
    try:
        feed = Feed(name=username)
        current_feed = aio.create_feed(feed)    
    except RequestError:
        raise HTTPException(status_code=404, detail="Feed already exists")
        
    return {"Feeds": current_feed}

@app.get("/get_feed")
def read_root(username: str, state: int):
    aio = Client(ADAFRUIT_IO_USERNAME, ADAFRUIT_IO_KEY)
    print(ADAFRUIT_IO_USERNAME, ADAFRUIT_IO_KEY)
    try:
        data = aio.feeds(username)
        aio.send_data(data.key, state)
        data = aio.receive(data.key)

    except RequestError:
        raise HTTPException(status_code=404, detail="Feed not found")
    
    return {"Message": "Successful"}

@app.get("/payment")
def payment(username: str):
    #Call the payment API
    headers = {
        "Authorization": f"Bearer {PAYMENT_SECRET_KEY}"
    }

    payload = {

            "tx_ref": f"{username}@{uuid.uuid4()}",
            "amount": "100",
            "currency": "NGN",
            "redirect_url":f"{ROOT_URL}/payment_callback",
            "meta": {
                "consumer_id": 23,
                "consumer_mac": "92a3-912ba-1192a"
            },

            "customer": {
                "email": "user@gmail.com",
                "phonenumber": "080****4528",
                "name": username
            },

            "customizations": {
                "title": "Open Energy"
            }
    }

    response = requests.post("https://api.flutterwave.com/v3/payments", headers=headers, json=payload)
    redirect_url = response.json().get("data").get("link")

    print(f"{ROOT_URL}/payment_callback")

    return RedirectResponse(url=redirect_url)

@app.get("/payment_callback") 
async def payment_callback(request: Request):
    # Get the request body
    body = request.query_params
    username = body.get("tx_ref").split("@")[0]

    if body.get("status") == "completed":
        url = f"{ROOT_URL}/get_feed?username={username}&state=1"
        return RedirectResponse(url=url)
    else:
        return {"status": "Payment failed"}

if __name__ == "__main__":
    import uvicorn
    #use uvicorn to run the app on localhost and reload the server when the code changes
    uvicorn.run(app, host="localhost", port=8000, reload=True)