from fastapi import HTTPException

invalid_username_or_password = HTTPException(status_code=400, detail="Invalid username or password")
invalid_credential = HTTPException(status_code=401,detail="Could not validate credentials",headers={"WWW-Authenticate":"Bearer"})
no_content = HTTPException(status_code=204,detail="No Content")
no_stock = HTTPException(status_code=400,detail="No Stock left")