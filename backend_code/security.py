import os
from datetime import datetime, timedelta
import bcrypt
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from dotenv import load_dotenv
from backend_code.database import db_state

load_dotenv()

JWT_SECRET_KEY=os.environ.get("JWT_SECRET_KEY", "fallback-secret-change-me")
ALGORITHM=os.environ.get("ALGORITHM","HS256")
ACCESS_TOKEN_EXPIRE_MINUTES=int(os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES",120))

oauth2_schema=OAuth2PasswordBearer(tokenUrl="authorize")

def verify_password(plain_password:str, hashed_password:str):
    """
    Needed during Authorization
    """
    password__bytes=plain_password.encode('utf-8')[:72]
    hashed_password=hashed_password.encode('utf-8')
    return bcrypt.checkpw(password=password__bytes,hashed_password=hashed_password)

def get_password_hash(plain_password:str):
    """
    Needed during User Registration
    """
    password_bytes=plain_password.encode(encoding='utf-8')[:72]
    salt=bcrypt.gensalt()
    hashed_password=bcrypt.hashpw(password=password_bytes,salt=salt)
    return hashed_password.decode(encoding='utf-8')


def create_access_token(data:dict, expires_delta: timedelta|None=None):
    """
    Needed during Authorization
    """
    to_encode=data.copy()
    expire=datetime.utcnow()+(expires_delta if expires_delta is not None else timedelta(minutes=15))
    to_encode.update({'exp':expire})
    return jwt.encode(claims=to_encode,key=JWT_SECRET_KEY,algorithm=ALGORITHM)

async def get_current_user(token: str=Depends(dependency=oauth2_schema)):
    try:
        payload=jwt.decode(token=token,key=JWTError, algorithms=[ALGORITHM])
        username: str=payload.get('sub')
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Username Not Found in the Token",
                headers={"WWW-Authenticate":'Bearer'}
                )
    except JWTError:  # what if the validity timeout has happened
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate":"Bearer"}
        )
    
    # Validating if the user returned by the token really exists in the database
    user=await db_state.db.users.\
        find_one(filter={'username':username})  # we had inserted in the database while registering the user
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Username could not be located in the database",
            headers={"WWW-Authenticate":"Bearer"}
        )
    return user