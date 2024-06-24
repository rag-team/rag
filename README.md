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


### Testing document processing
To test document processing locally, create the `_Dokumentendump_` folder at top-level, and put some PDF file into it. Then call
```
python -m server.process_document *YOUR_DOCUMENT*
python3 -m server.process_document ING_Herauslagekriterien.pdf
```

### Setting local folder for database and logs
The local folder for database and logs should be set in docker compose:
```
volumes:
      - /local/path:/server_data:rw
      - ...
```

### This is something Jan added to the readme
```pip install llama-cpp-python  --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cu121 --upgrade --force-reinstall --no-cache-dir```
