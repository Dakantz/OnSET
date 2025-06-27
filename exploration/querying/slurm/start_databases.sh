#!/usr/bin/env bash
#SBATCH --time=24:00:00
#SBATCH --partition=hcc

if [ -z "$SLURM_ARRAY_TASK_ID" ]; then
    echo "SLURM_ARRAY_TASK_ID is not set. Please run this script as a SLURM array job."
    SLURM_ARRAY_TASK_ID=0  # Default to 0 if not set
fi

export PGPORT=5434

pg_ctl -D /home/funkeydunkey/postgresql/data -l /home/funkeydunkey/postgresql/server.log start

redis-server &

# Reverse the following commands!
#ALTER USER funkeydunkey PASSWORD 'postgresql';DROP DATABASE postgres;CREATE DATABASE funkeydunkey;
# Reverse command:
#
#psql -U funkeydunkey -c "ALTER USER postgres PASSWORD 'postgresql'; DROP DATABASE funkeydunkey; CREATE DATABASE postgres;"
#psql -U funkeydunkey -c "CREATE ROLE postgres SUPERUSER CREATEDB CREATEROLE INHERIT LOGIN PASSWORD 'postgres';";

createdb onset
createdb onset-dbpedia
createdb onset-uniprot
createdb onset-bto
createdb onset-dnb
createdb onset-yago

# qlever
# /home/funkeydunkey/OnSET/qlever/build/ServerMain

#pushd ../../../docker
#for db in dbpedia uniprot bto dnb; do
#    pushd "${db}-data"
#    qlever start
#done
#popd

start_db() {
    local db_name=$1
    # if number -> 0: dbpedia, 1: bto, 2: uniprot, 3: dnb
    # else if string -> dbpedia, bto, uniprot, dnb
    case $db_name in
        0) db_name="dbpedia" ;;
        1) db_name="bto" ;;
        2) db_name="uniprot" ;;
        3) db_name="yago" ;;
        dbpedia|bto|uniprot|yago) ;;  # valid names
        *) echo "Invalid database name: $db_name"; exit 1 ;;
    esac
    echo "Starting $db_name database..."
    # from "querying" directory
    pushd ../../docker/"$db_name-data"
    qlever start
    popd
    echo "$db_name database started."
}

stop_db() {
    local db_name=$1
    # if number -> 0: dbpedia, 1: bto, 2: uniprot, 3: dnb
    # else if string -> dbpedia, bto, uniprot, dnb
    case $db_name in
        0) db_name="dbpedia" ;;
        1) db_name="bto" ;;
        2) db_name="uniprot" ;;
        3) db_name="yago" ;;
        dbpedia|bto|uniprot|yago) ;;  # valid names
        *) echo "Invalid database name: $db_name"; exit 1 ;;
    esac
    echo "Stopping $db_name database..."
    # from "querying" directory
    pushd ../../docker/"$db_name-data"
    qlever stop
    popd
    echo "$db_name database stopped."
    pg_ctl stop -D /home/funkeydunkey/postgresql/data -l /home/funkeydunkey/postgresql/server.log start
}