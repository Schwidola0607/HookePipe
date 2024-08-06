# HookePipe

## Setup
First, install [Docker](https://docs.docker.com/engine/install/) if you haven't already. Then, do all the following commands in your terminal:

1. `docker compose up -d`.  
If you are using Mac ARM `PLATFORM=linux/arm64 docker compose up -d`
2. Once it is done running, use `docker-compose ps` to check on the status. Then, get the TCP port being used from the PORTS section. For example, if there is `2380/tcp, 0.0.0.0:50814->2379/tcp`, the TCP port would be `50814`.
3. That value should be the `etcd_port` in the topology.


## Important docker functions you can use

### General Docker Functions
- `docker compose down` - stop the docker compose
- `docker compose up -d` - start the docker compose

### Docker etcdctl Functions
- `docker-compose exec etcd-1 etcdctl --endpoints=http://localhost:2379 member list` - list all etcd nodes running
- `docker-compose exec etcd-1 etcdctl --endpoints=http://localhost:2379 endpoint health` - get details about etcd health
- `docker-compose exec etcd-1 etcdctl --endpoints=http://localhost:2379 get --prefix --keys-only ""` - list all keys in etcd