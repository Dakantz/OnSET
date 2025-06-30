# OnSET

## Live Demo

> In progress...

## Description

OnSET should enable a more explorative ontology querying experience for non-expert users, and to build a quick understanding of the scale and nature of a KG that is in use. The toolkit consists of multiple smaller systems, complimenting each other. We have three default views ready:

* a query view; where users can construct queries either from topics or from natural language prompts,
* the explorative view; enabling users to view the ontology as a whole, view sparse relations and explore the named instances, and
* the linked view; showing users the hierarchical ontology *and* topic model at the same time, creating a rich visualization of multiple dimensions within the ontology. 


## Setup instruction

1. Install Apache Fuseki such that you have a working `riot` command line tool (https://jena.apache.org/documentation/fuseki2/)
2. Setup a local `qlever` instance (https://github.com/ad-freiburg/qlever-control) (the used configurations can be found in `docker/bto-data` and `docker/dbpedia-data`), you should be able to just run from the `docker/*-data`-directories:
```bash
qlever get-data
qlever index
qlever start
```
3. Start auxiliary DB using `cd docker/onset-data && docker-compose up -d`
4. Backend setup:
   - install `uv` (https://docs.astral.sh/uv/getting-started/installation/)
   - install dependencies using `CMAKE_ARGS="-DGGML_CUDA=on" uv sync` (or `CMAKE_ARGS="-DGGML_METAL=on" uv sync` on Mac)
   - start backend (should initialize DB on first start) using the correct Python  installation using `python -m uvicorn api:app --reload --port 8001`
5. Frontend setup:
   - install a somewhat recent Node version
   - install dependencies by first `cd frontend && npm i -D`
   - then start the frontend using `npm run dev`
* Profit?



### Cluster setup instructions

* Download and build qlever

```
cd ~
git clone https://github.com/ad-freiburg/qlever.git
cd qlever/bin
cmake ..
cmake --build . --target IndexBuilderMain ServerMain -j
```

* Make postgres ready

```bash
cd ~
mkdir postgresql/data
cd postgresql/data
pg_ctl initdb -D .

pg_ctl -D . -l $HOME/postgresql/server.log -o "-p 5434 -k /tmp -i" start
```
then run:
```bash
createdb -U $USER -p 5434 $USER
psql -U $USER -p 5434 -c "ALTER USER postgres PASSWORD 'postgresql'; DROP DATABASE $USER; CREATE DATABASE postgres;"
psql -U $USER -p 5434  -c "CREATE ROLE postgres SUPERUSER CREATEDB CREATEROLE INHERIT LOGIN PASSWORD 'postgres';";
```
