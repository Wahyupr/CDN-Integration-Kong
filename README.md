
# Simple CDN Integration Python with Kong API Gateway

## Installation

Docker and Docker Compose must be installed. see documentation [here](https://docs.docker.com/compose/install/)

## Usage/Examples
```bash
  docker-compose up -d 
```
## Register and Login Konga

```bash
  localhost:1337
```

## Install 
```bash
  pip install flask
```
## Run Backend CDN and Integration automatic Create Services and Route Kong
```bash
  cd backend
  python3 api_cdn.py
```

## Notes
#### please adjust it for the host of the upstream server in your local area for integration Kong API, For Example in my local  use docker host
```
host.docker.internal
```


