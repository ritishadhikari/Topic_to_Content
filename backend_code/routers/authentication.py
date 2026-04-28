import logging
from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from backend_code.pydantic_schema import UserCreate, Token
from backend_code.database import db_state
from backend_code.security import (
    get_password_hash, verify_password, ACCESS_TOKEN_EXPIRE_MINUTES,
    create_access_token
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    datefmt="%Y:%m:%d %H:%M:%S"
)

logger=logging.getLogger(name="AuthRouter")
router=APIRouter(tags=["Authentication"])

@router.post(path="/register", status_code=status.HTTP_201_CREATED,)
async def register_user(user: UserCreate):
    logger.info(msg=f"Attemting to register user: {user.username}")
    existing_user=await db_state.db.users.find_one({"username":user.username})
    if existing_user is not None:
        logger.warning(msg=f"Registration failed. Username: {user.username} already exists in the database")
        raise HTTPException(status_code=400, detail="Username is already Registered")
    else:
        hashed_password=get_password_hash(plain_password=user.password)
        user_dict={"username":user.username,"hashed_password":hashed_password}
        await db_state.db.users.insert_one(document=user_dict)
        logger.info(msg=f"User {user.username} registered successfully.")
        return {"msg": "User created Successfully"}
    
@router.post(path="/authorize", response_model=Token, status_code=status.HTTP_200_OK)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm=Depends()):
    logger.info(f"Login attempt for user: {form_data.username}")
    user=await db_state.db.users.find_one({"username":form_data.username})
    
    if user is None or not verify_password(plain_password=form_data.password,hashed_password=user['hashed_password']):
        logger.warning(f"Failed login attempt for user: {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate":"Bearer"}
        )
    else:
        access_token_expires=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token=create_access_token(data={'sub':form_data.username},expires_delta=access_token_expires)
        logger.info(f"Successful login for user: {form_data.username}")
        return {"access_token":access_token,"token_type":"bearer"}

    
