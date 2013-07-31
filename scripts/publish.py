#!/usr/bin/python
import sys
import subprocess
import re

username = sys.argv[1]
password = sys.argv[2]
existing_experiment = sys.argv[3]
experiment_name = sys.argv[4]
experiment_id = sys.argv[5]
existing_dataset = sys.argv[6]
dataset_name = sys.argv[7]
dataset_id = sys.argv[8]
'''
files = sys.argv[9]
logfile = sys.argv[10]
'''

datafile_metadata = ""
experiment_response_id = ""
dataset_response_id = ""
afile = ""
curl_cmd = subprocess.check_output(["which", "curl"]).rstrip("\n")
file_cmd = subprocess.check_output(["which", "file"]).rstrip("\n")
md5sum_cmd = subprocess.check_output(["which", "md5sum"]).rstrip("\n")
credential = "{0}:{1}".format(username, password)

mytardis_host = "http://staging-cvl-emap-mytardis.intersect.org.au"
content_header = "Content-Type: application/json"
accept_header = "Accept: application/json"

# regex expressions
experiment_id_regex = re.compile(r"Location.*experiment/(\d+)/", re.MULTILINE)
dataset_id_regex = re.compile(r"Location.*dataset/(\d+)/", re.MULTILINE)

# create a new experiment and return id
def create_experiment(name, description="test experiment", institution="The University of Sydney"):
    data = '{{"title":"{0}", "description":"{1}", "institution_name":"{2}"}}'.format(name, description, institution)
    url = "{base_url}/api/v1/experiment/".format(base_url = mytardis_host)

    response_header = subprocess.check_output([curl_cmd, "-s", "-i", "-H", content_header, "-H", accept_header, "-X", "POST", "-d", data, "-u", credential, url])
    return(experiment_id_regex.search(response_header).group(1))

# create a new dataset and return id
def create_dataset(description, experiment_id, immutable="false"):
    url = "{base_url}/api/v1/dataset/".format(base_url = mytardis_host)
    experiment_uri = "/api/v1/experiment/{0}/".format(experiment_id)
    data = '{{"description":"{0}", "experiments":["{1}"], "immutable":"{2}"}}'.format(description, experiment_uri, immutable)
    response_header = subprocess.check_output([curl_cmd, "-s", "-i", "-H", content_header, "-H", accept_header, "-X", "POST", "-d", data, "-u", credential, url])
    return(dataset_id_regex.search(response_header).group(1))

def push_file(path, filename, dataset_id):
    url = "{base_url}/api/v1/dataset_file/".format(base_url = mytardis_host)
    dataset_uri = "/api/v1/dataset/{0}/".format(dataset_id)
    md5sum = subprocess.check_output([md5sum_cmd, path]).split()[0]
    size = os.stat(path).st_size
    mimetype = subprocess.check_output([file_cmd, "-i", "-b", path]).split(";")[0]
    metadata = '{"dataset":"{0}", "filename":"{1}", "md5sum":"{2}", "size":"{3}", "mimetype":"{4}"}'.format(dataset_uri, filename, md5sum, size, mimetype)

    try:
        subprocess.check_call([curl_cmd, "-s", "-F", "attached_file={0}".format(path), "-F", "json-data={0}".format(metadata), "-u", credential, url])
    except:
        print("failed to push file")

def experiment_exists(id):
    url = "{base_url}/api/v1/experiment/{id}/?format=json".format(base_url = mytardis_host, id = id)

    try:
        response = subprocess.check_output([curl_cmd, "-s", "-u", credential, url])

        if response:
            return(True)
        else:
            return(False)
    except:
        print("failed to check experiment")


def dataset_exists(id):
    url = "{base_url}/api/v1/dataset/{id}/?format=json".format(base_url = mytardis_host, id = id)

    try:
        response = subprocess.check_output([curl_cmd, "-s", "-u", credential, url])

        if response:
            return(True)
        else:
            return(False)
    except:
        print("failed to check dataset")

print(create_dataset(dataset_name, experiment_id))