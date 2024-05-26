## How to develop?
Use `uvicorn main:app --reload` inside the server directory to start the server.

Use `streamlit run app.py` inside the client directory to start the client (local streamlit server).

## Using docker
Build and start a local Docker network for the server:
```
$ cd server
$ docker compose up server
```

Please move the networks folder to top-level of the repository.
