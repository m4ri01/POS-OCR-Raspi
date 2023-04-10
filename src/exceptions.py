from fastapi import HTTPException

invalid_username_or_password = HTTPException(status_code=400, detail="Invalid username or password")
invalid_credential = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Could not validate credentials",headers={"WWW-Authenticate":"Bearer"})