import secrets
from fastapi import FastAPI, Depends, status
from fastapi.exceptions import HTTPException
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from os import listdir, getenv
from pydantic import BaseModel
from sqlite3 import Error
import sqlite3
import roner
import json
import os

print("Loading the Romanian NER model")
nlp = roner.NER()

class TextToAnnotate(BaseModel):
    text: str

app = FastAPI()

security = HTTPBasic()


def create_connection():
    conn = None;
    try:
        conn = sqlite3.connect(':memory:')       # create a database in RAM
        return conn
    except Error as e:
        print(e)

def create_table(conn):
    try:
        sql_create_table = """ CREATE TABLE IF NOT EXISTS strings (
                                        id integer PRIMARY KEY,
                                        value text NOT NULL
                                    ); """
        c = conn.cursor()
        c.execute(sql_create_table)
    except Error as e:
        print(e)

def string_exists_or_insert(conn, string):
    try:
        sql = ''' SELECT * FROM strings WHERE value=? '''
        cur = conn.cursor()
        cur.execute(sql, (string,))

        rows = cur.fetchall()

        if rows:
            return False
        else:
            sql = ''' INSERT INTO strings(value) VALUES(?) '''
            cur.execute(sql, (string,))
            conn.commit()
            return True
    except Error as e:
        print(e)

# create a database connection
conn = create_connection()
# create table
create_table(conn)


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
    exists = string_exists_or_insert(conn, document.text)

    if exists:
        doc = nlp(document.text)
        ent_label_list = []
        for x in doc[0]["words"]:
            if x["tag"] not in "O":
                ent_label_list.append({"label": x["tag"], "word": x["text"], "start_offset": x["start_char"], "end_offset": x["end_char"]})

    else:
        ent_label_list = []

    response = json.dumps(ent_label_list)
    return response
