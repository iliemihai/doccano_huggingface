# https://linuxize.com/post/bash-check-if-file-exists/#check-if-file-does-not-exist

echo "Starting with local huggingface model"

uvicorn app.main:app --host 0.0.0.0 --port 8080
