#!/usr/bin/python
import sys
import subprocess

username = sys.argv[1]
password = sys.argv[2]
'''
experiment_exists = sys.argv[3]
experiment_name = sys.argv[4]
experiment_id = sys.argv[5]
dataset_exists = sys.argv[6]
dataset_name = sys.argv[7]
dataset_id = sys.argv[8]
files = sys.argv[9]
logfile = sys.argv[10]
'''

datafile_metadata = ""
experiment_response_id = ""
dataset_response_id = ""
afile = ""
curl_cmd = subprocess.check_output(["which", "curl"]).rstrip('\n')
credential = "{0}:{1}".format(username, password)

mytardis_host = "http://staging-cvl-emap-mytardis.intersect.org.au"
content_header = "Content-Type: application/json"
accept_header = "Accept: application/json"

def create_experiment(name, description, institution):
    data = "{{'title':'{0}', 'description':'{1}', 'institution_name':'{2}'}}".format(name, description, institution)
    print(data)
    url = "{base_url}/api/v1/experiment/".format(base_url = mytardis_host)
    exp_location = subprocess.check_output([
    	curl_cmd,
    	"-s",
    	"-H",
    	content_header,
    	"-H",
    	accept_header,
    	"-X POST",
    	"-d",
    	data,
    	"-u",
    	credential,
    	url
    ])
    return(exp_location)


output = create_experiment("test1", "test experiment 1", "The University of Sydney")

print(output)