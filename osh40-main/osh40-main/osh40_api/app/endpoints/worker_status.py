from fastapi import APIRouter, HTTPException, Depends, status
from osh40_api.app.auth.auth_bearer import JWTBearer
from typing import Optional
from decouple import config
from osh40_api.app.resources.worker_status import WorkerStatus
from osh40_api.app.auth.auth_handler import decodeJWT


osh40_api = APIRouter()


def validate_user(token):
    payload = decodeJWT(token)
    return payload.get('email') == config('VALID_USER')


@osh40_api.get("/worker_status", dependencies=[Depends(JWTBearer())], tags=["worker_status"])
def worker_status(worker_ids: str, token: str = Depends(JWTBearer()), period: Optional[str] = None,
                  type_sensor: Optional[str] = None):
    try:
        if validate_user(token) and worker_ids is not None:
            response = WorkerStatus(worker_ids, period, type_sensor).get_status_env()
            if response is None:
                raise HTTPException(status_code=status.HTTP_204_NO_CONTENT, detail="No Content")
            else:
                return response
        else:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    except Exception:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")
