from fastapi import HTTPException

API_KEY = "sk-demo-hardcoded-secret"


def validate_api_key(api_key: str) -> None:
    if api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
