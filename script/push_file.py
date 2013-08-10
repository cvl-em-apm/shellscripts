#!/usr/bin/env python
# push_file.py
# Usage:
# python push_file.py <ApiKey file> <experiment title> <dataset description> <file to push>

import sys
import subprocess
import re
import os
import json
import ConfigParser

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


key_file = sys.argv[1]
experiment_title = sys.argv[2]
dataset_description = sys.argv[3]
file_path = sys.argv[4]
curl_cmd = check_output(["which", "curl"]).rstrip("\n")
file_cmd = check_output(["which", "file"]).rstrip("\n")
md5sum_cmd = check_output(["which", "md5sum"]).rstrip("\n")
credential = open(key_file, 'r').read()

# get mytardis host configuration
cvl_emap_conf = ConfigParser.SafeConfigParser()
cvl_emap_conf.read("/usr/local/etc/cvl_emap.conf")
mytardis_host = cvl_emap_conf.get('mytardis', 'url')

content_header = "Content-Type: application/json"
accept_header = "Accept: application/json"
auth_header = "Authorization: {0}".format(credential)

# regex expressions
experiment_uri_regex = re.compile(r"Location.*(/api/v1/experiment/\d+/)", re.MULTILINE)
dataset_uri_regex = re.compile(r"Location.*(/api/v1/dataset/\d+/)", re.MULTILINE)


# create a new experiment and return uri
def create_experiment(title, description="This is an experiment", institution_name="The University of Sydney"):
    data = '{{"title":"{0}", "description":"{1}", "institution_name":"{2}"}}'.format(title, description, institution_name)
    url = "{base_url}/api/v1/experiment/".format(base_url=mytardis_host)

    response_header = check_output([curl_cmd, "-s", "-i", "-H", content_header, "-H", accept_header, "-H", auth_header, "-X", "POST", "-d", data, url])
    return(experiment_uri_regex.search(response_header).group(1))


# create a new dataset and return uri
def create_dataset(description, experiment_uri, immutable="false"):
    data = '{{"description":"{0}", "experiments":["{1}"], "immutable":{2}}}'.format(description, experiment_uri, immutable)
    url = "{base_url}/api/v1/dataset/".format(base_url=mytardis_host)

    response_header = check_output([curl_cmd, "-s", "-i", "-H", content_header, "-H", accept_header, "-H", auth_header, "-X", "POST", "-d", data, url])
    return(dataset_uri_regex.search(response_header).group(1))


# push one file
def push_file(path, dataset_uri, new_filename=None):
    url = "{base_url}/api/v1/dataset_file/".format(base_url=mytardis_host)
    md5sum = check_output([md5sum_cmd, path]).split()[0]
    size = os.stat(path).st_size
    mimetype = check_output([file_cmd, "-i", "-b", path]).split(";")[0]

    if new_filename is None:
        metadata = '{{"dataset":"{0}", "filename":"{1}", "md5sum":"{2}", "size":"{3}", "mimetype":"{4}"}}'.format(dataset_uri, os.path.basename(path), md5sum, size, mimetype)
    else:
        metadata = '{{"dataset":"{0}", "filename":"{1}", "md5sum":"{2}", "size":"{3}", "mimetype":"{4}"}}'.format(dataset_uri, new_filename, md5sum, size, mimetype)

    response_header = None

    try:
        response_header = check_output([curl_cmd, "-s", "-i", "-F", "attached_file={0}".format(path), "-F", "json_data={0}".format(metadata), "-H", auth_header, url])
    except:
        print("Server error")


# check experiment by title, return uri if found, false if not
def experiment_exists(title):
    url = "{base_url}/api/v1/experiment/?format=json".format(base_url=mytardis_host)

    response = None

    try:
        response = check_output([curl_cmd, "-s", "-H", auth_header, url])
    except:
        print("Server error")

    if response:
        response_dict = json.loads(response)
        experiment_list = response_dict['objects']

        if len(experiment_list) == 0:
            return(False)

        for experiment in experiment_list:
            if experiment['title'] == title:
                return(experiment['resource_uri'])

        # No experiment match
        return(False)
    else:
        print("Authentication failed")
        return(False)


# check dataset by description, return uri if found, false if not
def dataset_exists(description):
    url = "{base_url}/api/v1/dataset/?format=json".format(base_url=mytardis_host)

    response = None

    try:
        response = check_output([curl_cmd, "-s", "-H", auth_header, url])
    except:
        print("Server error")

    if response:
        response_dict = json.loads(response)
        dataset_list = response_dict['objects']

        if len(dataset_list) == 0:
            return(False)

        for dataset in dataset_list:
            if dataset['description'] == description:
                return(dataset['resource_uri'])

        # No dataset match
        return(False)
    else:
        print("Authentication failed")
        return(False)

# Tests
'''
# test command line usage:
# python push_file.py ~/Downloads/seanl.key "test experiment 4" "test dataset 15" ../Makefile.in

print(experiment_exists(experiment_title))
print(dataset_exists(dataset_description))
experiment_uri = create_experiment(experiment_title)
dataset_uri = create_dataset(dataset_description, experiment_uri)
dataset_uri = dataset_exists(dataset_description)
push_file(file_path, dataset_uri)
sys.exit()
'''

# main
experiment_uri = experiment_exists(experiment_title)
dataset_uri = dataset_exists(dataset_description)

if experiment_uri:
    if dataset_uri:
        push_file(file_path, dataset_uri)
    else:
        push_file(file_path, create_dataset(dataset_description, experiment_uri))
else:
    push_file(file_path, create_dataset(dataset_description, create_experiment(experiment_title)))
