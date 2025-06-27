#!/usr/bin/env bash

set -e

create_conda_env() {
    conda env create -f environment.yaml
}

create_databases() {
    mkdir -p ~/postgresql/data
    initdb -D ~/postgresql/data

    pg_ctl -D ${HOME}/postgresql/data -l ${HOME}/postgresql/server.log start
    createuser -s postgres

    POSTGRES_USER="postgres"
    export PGUSER="$POSTGRES_USER"

    psql=(psql --username "$POSTGRES_USER")

    # Create the 'template_postgis' template db
    "${psql[@]}" <<- 'EOSQL'
    CREATE DATABASE template_postgis IS_TEMPLATE true;
EOSQL

    # Load PostGIS into both template_database and $POSTGRES_DB
    for DB in template_postgis "$POSTGRES_DB"; do
        echo "Loading PostGIS extensions into $DB"
        "${psql[@]}" --dbname="$DB" <<-'EOSQL'
            CREATE EXTENSION IF NOT EXISTS postgis;
            CREATE EXTENSION IF NOT EXISTS postgis_topology;
            CREATE EXTENSION IF NOT EXISTS fuzzystrmatch;
            CREATE EXTENSION IF NOT EXISTS postgis_tiger_geocoder;
            CREATE EXTENSION  IF NOT EXISTS vector;
EOSQL
    done

    "${psql[@]}" <<- 'EOSQL'
    CREATE DATABASE onset;
EOSQL
}

add_to_path() {
    local dir="$1"
    if [[ -d "$dir" ]]; then
        export PATH="$PATH:$dir"
        # if bash, add to ~/.bashrc
        if [[ -n "$BASH_VERSION" ]]; then
            echo "# >>> $dir >>>" >> ~/.bashrc
            echo "export PATH=\"\$PATH:$dir\"" >> ~/.bashrc
            echo "# <<< $dir <<<" >> ~/.bashrc
        elif [[ -n "$ZSH_VERSION" ]]; then
            echo "# >>> $dir >>>" >> ~/.zshrc
            echo "export PATH=\"\$PATH:$dir\"" >> ~/.zshrc
            echo "# <<< $dir <<<" >> ~/.zshrc
        fi
    else
        echo "Directory $dir does not exist."
    fi
}

install_qlever() {
    git clone https://github.com/ad-freiburg/qlever.git

    mkdir qlever/build
    pushd qlever/build

    export CC="${CONDA_PREFIX}/bin/gcc"
    export CXX="${CONDA_PREFIX}/bin/g++"

    cmake -DCMAKE_BUILD_TYPE=Release \
            -DCMAKE_C_COMPILER="${CC}" \
            -DCMAKE_CXX_COMPILER="${CXX}" \
            -DLOGLEVEL=INFO -DUSE_PARALLEL=true -D_NO_TIMING_TESTS=ON -DCMAKE_POLICY_VERSION_MINIMUM=3.5 -GNinja ..

    cmake --build . --target IndexBuilderMain --config Release
    cmake --build . --target ServerMain --config Release

    add_to_path "$(pwd)"

    popd
}


install_jena() {
    wget https://dlcdn.apache.org/jena/binaries/apache-jena-5.4.0.zip
    unzip apache-jena-5.4.0.zip
    rm apache-jena-5.4.0.zip
    # add apache-jena-5.4.0/bin to PATH
    add_to_path "$(pwd)/apache-jena-5.4.0/bin"
}


echo "Create Conda environment? [y/N]"
read -r create_conda_env_choice
if [[ "$create_conda_env_choice" == "y" || "$create_conda_env_choice" == "Y" ]]; then
    create_conda_env
else
    echo "Skipping Conda environment creation."
fi

echo "Create Postgres and PostGIS databases? [y/N]"
read -r create_databases_choice
if [[ "$create_databases_choice" == "y" || "$create_databases_choice" == "Y" ]]; then
    echo "Creating Postgres and PostGIS databases..."
    create_databases
else
    echo "Skipping database creation."
fi

echo "Install Qlever? [y/N]"
read -r install_qlever_choice
if [[ "$install_qlever_choice" == "y" || "$install_qlever_choice" == "Y" ]]; then
    install_qlever
    echo "Qlever installed successfully."
    echo "Please restart your terminal or run 'source ~/.bashrc' or 'source ~/.zshrc' to update your PATH."
else
    echo "Skipping Qlever installation."
fi

echo "Install Apache Jena? [y/N]"
read -r install_jena_choice
if [[ "$install_jena_choice" == "y" || "$install_jena_choice" == "Y" ]]; then
    install_jena
    echo "Apache Jena installed successfully."
    echo "Please restart your terminal or run 'source ~/.bashrc' or 'source ~/.zshrc' to update your PATH."
else
    echo "Skipping Apache Jena installation."
fi