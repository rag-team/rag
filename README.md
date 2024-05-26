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

Note: there is currently a bug where the database credentials are off. After building, go into the database container and set permissions for the mysql user manually. Afterwards restart the server docker again.
```
$ docker ps | grep mysql
$ docker exec -it CONTAINER_ID /bin/bash
$ mysql -p
  Password: (refer to docker file)
$ GRANT ALL PRIVILEGES ON *.* TO 'mysql':'%';
$ FLUSH PRIVILEGES;
```
