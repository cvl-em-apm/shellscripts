#!/usr/bin/env python
import sys
import subprocess
import re
import os
import json

def check_output(*popenargs, **kwargs):
    if 'stdout' in kwargs:
        raise ValueError('stdout argument not allowed, it will be overridden.')
    process = subprocess.Popen(stdout=subprocess.PIPE, *popenargs, **kwargs)
    output, unused_err = process.communicate()
    retcode = process.poll()
    if retcode:
        cmd = kwargs.get("args")
        if cmd is None:
            cmd = popenargs[0]
        raise CalledProcessError(retcode, cmd, output=output)
    return output

existing_experiment = sys.argv[1]
experiment_name = sys.argv[2]
experiment_url = sys.argv[3]
existing_dataset = sys.argv[4]
dataset_name = sys.argv[5]
dataset_url = sys.argv[6]
files = sys.argv[7]

datafile_metadata = ""
experiment_response_id = ""
dataset_response_id = ""
curl_cmd = check_output(["which", "curl"]).rstrip("\n")
file_cmd = check_output(["which", "file"]).rstrip("\n")
md5sum_cmd = check_output(["which", "md5sum"]).rstrip("\n")

mytardis_host = "http://localhost:8000"
content_header = "Content-Type: application/json"
accept_header = "Accept: application/json"

apikey = ""
apikey_file = "/data/keys/seanl.key"
with open(apikey_file, 'r') as f:
  apikey = f.readline().splitlines()[0]

authorization_header = 'Authorization: {0}'.format(apikey)

# regex expressions
experiment_id_regex = re.compile(r"Location.*experiment/(\d+)/", re.MULTILINE)
dataset_id_regex = re.compile(r"Location.*dataset/(\d+)/", re.MULTILINE)
experiment_url_regex = re.compile(r'{base_url}/experiment/view/(\d+)/'.format(base_url = mytardis_host))
dataset_url_regex = re.compile(r'{base_url}/dataset/(\d+)'.format(base_url = mytardis_host))

# create a new experiment and return id
def create_experiment(name, description="test experiment", institution="The University of Sydney"):
    data = '{{"title":"{0}", "description":"{1}", "institution_name":"{2}"}}'.format(name, description, institution)
    url = "{base_url}/api/v1/experiment/".format(base_url = mytardis_host)
    response_header = check_output([curl_cmd, "-s", "-i", "-H", authorization_header, "-H", content_header, "-H", accept_header, "-X", "POST", "-d", data, url])

    return(experiment_id_regex.search(response_header).group(1))

# create a new dataset and return id
def create_dataset(description, experiment_id, immutable="false"):
    url = "{base_url}/api/v1/dataset/".format(base_url = mytardis_host)
    experiment_uri = "/api/v1/experiment/{0}/".format(experiment_id)
    data = '{{"description":"{0}", "experiments":["{1}"], "immutable":{2}}}'.format(description, experiment_uri, immutable)
    
    response_header = check_output([curl_cmd, "-s", "-i", "-H", content_header, "-H", accept_header, "-H", authorization_header, "-X", "POST", "-d", data, url])
    return(dataset_id_regex.search(response_header).group(1))

# pushes one file
def push_file(file_path, dataset_id, old_filename, new_filename):
    url = "{base_url}/api/v1/dataset_file/".format(base_url = mytardis_host)
    dataset_uri = "/api/v1/dataset/{0}/".format(dataset_id)
    md5sum = check_output([md5sum_cmd, file_path]).split()[0]
    size = os.stat(file_path).st_size
    mimetype = check_output([file_cmd, "-i", "-b", file_path]).split(";")[0]
    if new_filename is None:
        metadata = { "dataset": dataset_uri, "filename": old_filename, "md5sum": md5sum, "size": size, "mimetype": mimetype }
    else:
        metadata = {
            "dataset": dataset_uri,
            "filename": new_filename,
            "md5sum": md5sum,
            "size": size,
            "mimetype": mimetype,
            "parameter_sets": [
                {
                "schema": "http://www.datafile.com/",
                "parameters": [
                    {
                    "name": "orig_filename",
                    "value": old_filename
                    }
                ]
                }
            ]
        }

    try:
        check_output([curl_cmd, "-s", "-F", "attached_file=@{0}".format(file_path), "-F", "json_data={0}".format(json.dumps(metadata)), "-H", authorization_header, url])
    except:
        print("failed to push file")

def experiment_exists(id):
    url = "{base_url}/api/v1/experiment/{id}/?format=json".format(base_url = mytardis_host, id = id)
 
    try:
        response = check_output([curl_cmd, "-s", "-H", authorization_header, url])
 
        if response:
            return(True)
        else:
            return(False)
    except:
        print("failed to check experiment")
   
   
def dataset_exists(id):
    url = "{base_url}/api/v1/dataset/{id}/?format=json".format(base_url = mytardis_host, id = id)
 
    try:
        response = check_output([curl_cmd, "-s", "-H", authorization_header, url])
 
        if response:
            return(True)
        else:
            return(False)
    except:
        print("failed to check dataset")

# convert arg into boolean
def has_experiment():
    if existing_experiment == "true":
        return(True)
    elif existing_experiment == "false":
        return(False)

def has_dataset():
    if existing_dataset == "true":
        return(True)
    elif existing_dataset == "false":
        return(False)

# read output.txt file containing directories of files
def read_files():
    content = None
    with open(files, "r") as f:
        content = f.read().splitlines()
    return content

# loop through the result of output.txt and pushes files sequentially
def push_datafiles(dataset_id):
    for metadata in read_files():
        if metadata.strip():
            file_path, orig_file_name, new_file_name = metadata.split(';')
            if new_file_name:
                # append original file extension
                orig_file_ext = os.path.splitext(orig_file_name)[1]
                new_file_ext = os.path.splitext(new_file_name)[1]
                if orig_file_ext != new_file_ext:
                    new_file_name = "{0}{1}".format(new_file_name, orig_file_ext)
                push_file(file_path, dataset_id, orig_file_name, new_file_name)
            else:
                push_file(file_path, dataset_id, orig_file_name, None)
       
def main():
    if has_experiment():
        print "Pushing to an existing experiment"
        experiment_id = experiment_url_regex.search(experiment_url).group(1)
        
        if has_dataset():
            print "Pushing to an existing dataset"
            dataset_id = dataset_url_regex.search(dataset_url).group(1)
            print "Pushing datafiles"
            push_datafiles(dataset_id)
        else:
            print "Creating new dataset"
            dataset_id = create_dataset(dataset_name, experiment_id)
            print "Pushing datafiles"
            push_datafiles(dataset_id)
    else:
        print "Creating new experiment and dataset"
        experiment_id = create_experiment(experiment_name)
        dataset_id = create_dataset(dataset_name, experiment_id)
        print "Pushing datafiles"
        push_datafiles(dataset_id)

def debug():
    print "Printing all relevant parameters"
    print existing_experiment
    print experiment_name
    print experiment_url
    print existing_dataset
    print dataset_name
    print dataset_url
      
main()
