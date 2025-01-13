#from fastapi import FastAPI

#app = FastAPI()

#@app.post("/m400completed")
#async def m400_completed():
#    print("Received M400 completed event")

#if __name__ == "__main__":
#    import uvicorn
#    uvicorn.run(app, host="0.0.0.0", port=5001)

import logging
from fastapi import FastAPI

app = FastAPI()

# Configure logging
logging.basicConfig(filename="fastapi.log", level=logging.INFO, format='%(asctime)s %(message)s')

@app.post("/m400completed")
async def m400_completed():
    logging.info("Received M400 completed event")
    # Add your code here to update the VR tracker position

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5001)
