# HookePipe

## Setup
First, install [Docker](https://docs.docker.com/engine/install/) if you haven't already. Then, do all the following commands in your terminal:

1. `docker compose up -d`.  
If you are using Mac ARM `PLATFORM=linux/arm64 docker compose up -d`
2. Run the test script by running `sh tests/basic.sh <arg>` where arg is the number of nodes you want to create


## Important docker functions you can use

### General Docker Functions
- `docker compose down` - stop the docker compose
- `docker compose up -d` - start the docker compose

### Docker etcdctl Functions
- `docker-compose exec etcd-1 etcdctl --endpoints=http://localhost:2379 member list` - list all etcd nodes running
- `docker-compose exec etcd-1 etcdctl --endpoints=http://localhost:2379 endpoint health` - get details about etcd health
- `docker-compose exec etcd-1 etcdctl --endpoints=http://localhost:2379 get --prefix --keys-only ""` - list all keys in etcd