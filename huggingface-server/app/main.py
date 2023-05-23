import secrets
from fastapi import FastAPI, Depends, status
from fastapi.exceptions import HTTPException
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel
# from auth import has_access
import roner
import json
import os
from os import listdir, getenv

print("Loading the Romanian NER model")
nlp = roner.NER()

class TextToAnnotate(BaseModel):
    text: str

app = FastAPI()

security = HTTPBasic()

def has_access(credentials: HTTPBasicCredentials = Depends(security)):
    correct_username = secrets.compare_digest(credentials.username, os.getenv('HUGGINGFACE_USER'))
    correct_password = secrets.compare_digest(credentials.password, os.getenv('HUGGINGFACE_PASSWORD'))
    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username

# Try it out on http://localhost:8080/docs in your browser
@app.get('/get')
def get():
    return 'hello'

@app.post("/auto_annotate", dependencies=[Depends(has_access)])
async def auto_annotate(document: TextToAnnotate):
    doc = nlp(document.text)
    ent_label_list = []
    for x in doc[0]["words"]:
        if x["tag"] not in "O":
            ent_label_list.append({"label": x["tag"], "word": x["text"], "start_offset": x["start_char"], "end_offset": x["end_char"]})
            
    response = json.dumps(ent_label_list)
    return response
