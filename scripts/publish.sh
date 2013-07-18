#!/bin/bash

USERNAME=$1
PASSWORD=$2
EXPERIMENT_EXISTS=$3
EXPERIMENT_NAME=$4
EXPERIMENT_ID=$5
DATASET_EXISTS=$6
DATASET_NAME=$7
DATASET_ID=$8
FILES=$9
LOGFILE=$10

DATAFILE_METADATA=0
EXPERIMENT_RESPONSE_ID=0
DATASET_RESPONSE_ID=0
FILE=0

BASE_URI=""
CONTENT_HDR="Content-Type: application/json"
ACCEPT_HDR="Accept: application/json"

experiment=$(curl -s -u $USERNAME:$PASSWORD http://localhost:8000/api/v1/experiment/$EXPERIMENT_ID/?format=json)
dataset=$(curl -s -u $USERNAME:$PASSWORD http://localhost:8000/api/v1/dataset/$DATASET_ID/?format=json)

function create_experiment {
    title=$EXPERIMENT_NAME
    description="Auto generated text"
    institution="Monash University"

    exp_location=$(curl -s -H "$CONTENT_HDR" -H "$ACCEPT_HDR" -X POST -d "{\"title\":\"$title\",\"description\":\"$description\",\"institution_name\":\"$institution\"}" -u $USERNAME:$PASSWORD http://localhost:8000/api/v1/experiment/ | tail -2 | head -1)
    if [ $? != 0 ]; then
    {
        echo "Encountered a problem when creating new experiment"
        echo "$exp_location"
        exit 1
    } fi
    EXPERIMENT_RESPONSE_ID=$(echo "${exp_location%?}" | tr -d "/" | tr -d "\n" | tail -c 2)
}

function create_dataset {
    if [ $EXPERIMENT_EXISTS == "false" ]
    then
        EXPERIMENT_ID=$EXPERIMENT_RESPONSE_ID
    fi

    description=$DATASET_NAME
    uri="/api/v1/experiment/$EXPERIMENT_ID/"

    ds_location=$(curl -s -H "$CONTENT_HDR" -H "$ACCEPT_HDR" -X POST -d "{\"description\":\"$description\",\"experiments\":[\"$uri\"],\"immutable\":"false"}" -u $USERNAME:$PASSWORD http://localhost:8000/api/v1/dataset/ | tail -2 | head -1)
    if [ $? != 0 ]; then
    {
        echo "Encountered a problem when creating new dataset"
        echo "$ds_location"
        exit 1
    } fi
    DATASET_RESPONSE_ID=$(echo "${ds_location%?}" | tr -d "/" | tr -d "\n" | tail -c 2)
}

function get_datafile_metadata {
    echo "Retrieving metadata for file $FILE"

    if [ $DATASET_EXISTS == "false" ]
    then
        echo "No dataset exists - using created dataset ID"
        DATASET_ID=$DATASET_RESPONSE_ID
    fi

    if [ $? -eq 0 ]
    then
        mimetype=$(file -ib $FILE | cut -f1 -d ";")
        dataset_uri="/api/v1/dataset/$DATASET_ID/"
        md5sum=$(md5sum $FILE | cut -f1 -d " ")
        size=$(du -s $FILE | cut -f1)
        filename=$(ls $FILE)

        DATAFILE_METADATA="{\"dataset\":\"$dataset_uri\",\"filename\":\"$filename\",\"md5sum\":\"$md5sum\",\"size\":\"$size\",\"mimetype\":\"$mimetype\"}"
     else
        echo "Something went wrong when reading file metadata"
        exit 1
     fi
}

function push_datafile {
    for line in $(cat $FILES)
    do
        FILE=$(echo "$line" | cut -d";" -f1 )
        get_datafile_metadata
        curl -s -F attached_file=$FILES -F json_data=$DATAFILE_METADATA -u $USERNAME:$PASSWORD http://localhost:8000/api/v1/dataset_file/
    done

}

function check_experiment {
    if [ $EXPERIMENT_EXISTS == "true" ]
    then
        if [ -z "$experiment" ]
        then
            echo "No experiment on MyTardis - creating new experiment"
            create_experiment
            create_dataset
            push_datafile
        else
            echo "Experiment exists - checking if dataset exists"
            check_dataset
        fi
    else
        echo "Creating new experiment, dataset and pushing datafile"
        create_experiment
        create_dataset
        push_datafile
    fi
}

function check_dataset {
    if [ $DATASET_EXISTS == "true" ]
    then
        if [ -z "$dataset" ]
        then
            echo "No dataset on MyTardis - creating new dataset in experiment and pushing datafile"
            create_dataset
            push_datafile
        else
            echo "Found dataset - pushing datafiles"
            push_datafile
        fi
    else
        echo "No dataset specified - creating new"
        create_dataset
        push_datafile
    fi
}

function check_parameters {
    if [ $EXPERIMENT_EXISTS == "true" ]
    then
        if [ -z "$experiment" ]
        then
            echo "Could not find experiment with the specified ID"
            exit 1
        fi
    fi

    if [ $DATASET_EXISTS == "true" ]
    then
        if [ -z "$dataset" ]
        then
            echo "Could not find dataset with specified ID"
            exit 1
        fi
    fi
}

function init {
    check_parameters
    check_experiment
}

echo "Initializing"
init