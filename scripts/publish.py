#!/usr/bin/env python
import sys
import subprocess
import re
import os

apikey_file = sys.argv[1]
existing_experiment = sys.argv[2]
experiment_name = sys.argv[3]
experiment_url = sys.argv[4]
existing_dataset = sys.argv[5]
dataset_name = sys.argv[6]
dataset_url = sys.argv[7]
files = sys.argv[8]

datafile_metadata = ""
experiment_response_id = ""
dataset_response_id = ""
afile = ""
curl_cmd = subprocess.check_output(["which", "curl"]).rstrip("\n")
file_cmd = subprocess.check_output(["which", "file"]).rstrip("\n")
md5sum_cmd = subprocess.check_output(["which", "md5sum"]).rstrip("\n")

mytardis_host = "http://staging-cvl-emap-mytardis.intersect.org.au"
content_header = "Content-Type: application/json"
accept_header = "Accept: application/json"

apikey = ""
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
    print data
    url = "{base_url}/api/v1/experiment/".format(base_url = mytardis_host)
    print url
    print authorization_header
    response_header = subprocess.check_output([curl_cmd, "-s", "-i", "-H", authorization_header, "-H", content_header, "-H", accept_header, "-X", "POST", "-d", data, url])

    print response_header
    return(experiment_id_regex.search(response_header).group(1))

# create a new dataset and return id
def create_dataset(description, experiment_id, immutable="false"):
    url = "{base_url}/api/v1/dataset/".format(base_url = mytardis_host)
    experiment_uri = "/api/v1/experiment/{0}/".format(experiment_id)
    data = '{{"description":"{0}", "experiments":["{1}"], "immutable":{2}}}'.format(description, experiment_uri, immutable)
    
    response_header = subprocess.check_output([curl_cmd, "-s", "-i", "-H", content_header, "-H", accept_header, "-H", authorization_header, "-X", "POST", "-d", data, url])
    return(dataset_id_regex.search(response_header).group(1))

# pushes one file
def push_file(file, dataset_id, new_filename=None):
    url = "{base_url}/api/v1/dataset_file/".format(base_url = mytardis_host)
    dataset_uri = "/api/v1/dataset/{0}/".format(dataset_id)
    md5sum = subprocess.check_output([md5sum_cmd, file]).split()[0]
    size = os.stat(file).st_size
    mimetype = subprocess.check_output([file_cmd, "-i", "-b", file]).split(";")[0]
    if new_filename is None:
        metadata = '{{"dataset":"{0}", "filename":"{1}", "md5sum":"{2}", "size":"{3}", "mimetype":"{4}"}}'.format(dataset_uri, file, md5sum, size, mimetype)
    else:
        metadata = '{{"dataset":"{0}", "filename":"{1}", "md5sum":"{2}", "size":"{3}", "mimetype":"{4}"}}'.format(dataset_uri, new_filename, md5sum, size, mimetype)

    try:
        subprocess.check_call([curl_cmd, "-s", "-F", "attached_file={0}".format(file), "-F", "json_data={0}".format(metadata), "-H", authorization_header, url])
    except:
        print("failed to push file")

def experiment_exists(id):
    url = "{base_url}/api/v1/experiment/{id}/?format=json".format(base_url = mytardis_host, id = id)
 
    try:
        response = subprocess.check_output([curl_cmd, "-s", "-H", authorization_header, url])
 
        if response:
            return(True)
        else:
            return(False)
    except:
        print("failed to check experiment")
   
   
def dataset_exists(id):
    url = "{base_url}/api/v1/dataset/{id}/?format=json".format(base_url = mytardis_host, id = id)
 
    try:
        response = subprocess.check_output([curl_cmd, "-s", "-H", authorization_header, url])
 
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
            fp = metadata.split(';')
            if fp[1] is not None:
                push_file(fp[0], dataset_id, fp[1])
            else:
                push_file(fp[0], dataset_id)
       
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
