
import logging
import uvicorn
import sys
from decouple import config
from osh40_api.app.endpoints import worker_status
from fastapi import FastAPI, Request


logging.basicConfig(stream=sys.stdout, level=logging.ERROR,
                    format='[%(asctime)s] %(levelname)s - %(module)s: %(message)s',datefmt='%Y-%m-%d %H:%M:%S %z')

JWT_SECRET = config("OSH40_KEY_JWT")
JWT_ALGORITHM = config("JWT_ALGORITHM")


app = FastAPI(title='OSH 40', description='Predict health risk in work environment', version='0.0.1')
app.secret_key = JWT_SECRET


@app.middleware("http")
async def log_exceptions(request: Request, call_next):
    try:
        response = await call_next(request)
        return response
    except Exception as e:
        logging.error(f'[{request.method}]{request.url}: {e}')


app.include_router(worker_status.osh40_api)


if __name__ == "__main__":
    uvicorn.run("main:app", host="localhost", port=9000)
