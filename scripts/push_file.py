#!/usr/bin/env python
import sys
import subprocess
import re
import os

experiment_name = "Application Execution History"
key_file = sys.argv[1]
dataset_name = sys.argv[2]
file_name = sys.argv[3]
datafile_metadata = ""
experiment_response_id = ""
dataset_response_id = ""
afile = ""
curl_cmd = subprocess.check_output(["which", "curl"]).rstrip("\n")
file_cmd = subprocess.check_output(["which", "file"]).rstrip("\n")
md5sum_cmd = subprocess.check_output(["which", "md5sum"]).rstrip("\n")
credential = open(key_file, 'r').read()

mytardis_host = "http://localhost:8000"
content_header = "Content-Type: application/json"
accept_header = "Accept: application/json"
auth_header = "Authorization: {0}".format(credential)

# regex expressions
experiment_id_regex = re.compile(r"Location.*experiment/(\d+)/", re.MULTILINE)
dataset_id_regex = re.compile(r"Location.*dataset/(\d+)/", re.MULTILINE)
experiment_url_regex = re.compile(r'{base_url}/experiment/view/(\d+)/'.format(base_url = mytardis_host))
dataset_url_regex = re.compile(r'{base_url}/dataset/(\d+)'.format(base_url = mytardis_host))

# create a new experiment and return id
def create_experiment(name, description=experiment_name, institution="The University of Sydney")
    data = '{{"title":"{0}", "description":"{1}", "institution_name":"{2}"}}'.format(name, description, institution)
    url = "{base_url}/api/v1/experiment/".format(base_url = mytardis_host)

    response_header = subprocess.check_output([curl_cmd, "-s", "-i", "-H", content_header, "-H", accept_header, "-H", auth_header, "-X", "POST", "-d", data, url])
    return(experiment_id_regex.search(response_header).group(1))

# create a new dataset and return id
def create_dataset(description, experiment_id, immutable="false"):
    url = "{base_url}/api/v1/dataset/".format(base_url = mytardis_host)
    experiment_uri = "/api/v1/experiment/{0}/".format(experiment_id)
    data = '{{"description":"{0}", "experiments":["{1}"], "immutable":"{2}"}}'.format(description, experiment_uri, immutable)
    
    response_header = subprocess.check_output([curl_cmd, "-s", "-i", "-H", content_header, "-H", accept_header, "-H", auth_header, "-X", "POST", "-d", data, url])
    return(dataset_id_regex.search(response_header).group(1))

# push one file
def push_file(path, dataset_id, new_filename=None):
    url = "{base_url}/api/v1/dataset_file/".format(base_url = mytardis_host)
    dataset_uri = "/api/v1/dataset/{0}/".format(dataset_id)
    md5sum = subprocess.check_output([md5sum_cmd, path]).split()[0]
    size = os.stat(path).st_size
    mimetype = subprocess.check_output([file_cmd, "-i", "-b", path]).split(";")[0]
    if new_filename is None:
        metadata = '{{"dataset":"{0}", "filename":"{1}", "md5sum":"{2}", "size":"{3}", "mimetype":"{4}"}}'.format(dataset_uri, os.path.basename(path), md5sum, size, mimetype)
    else:
        metadata = '{{"dataset":"{0}", "filename":"{1}", "md5sum":"{2}", "size":"{3}", "mimetype":"{4}"}}'.format(dataset_uri, new_filename, md5sum, size, mimetype)

    try:
        subprocess.check_call([curl_cmd, "-s", "-F", "attached_file={0}".format(file), "-F", "json_data={0}".format(metadata), "-H", auth_header, url])
    except:
        print("failed to push file")

def experiment_exists(name):
    url = "{base_url}/api/v1/experiment/?format=json".format(base_url = mytardis_host)

    try:
        response = subprocess.check_output([curl_cmd, "-s", "-H", auth_header, url])

        if response:
            return(True)
        else:
            return(False)
    except:
        print("failed to check experiment")


def dataset_exists(name):
    url = "{base_url}/api/v1/dataset/{id}/?format=json".format(base_url = mytardis_host, id = id)

    try:
        response = subprocess.check_output([curl_cmd, "-s", "-H", auth_header, url])

        if response:
            return(True)
        else:
            return(False)
    except:
        print("failed to check dataset")

print(experiment_exists(experiment_name))
