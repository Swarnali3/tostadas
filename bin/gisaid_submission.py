#!/usr/bin/env python3

import sys
import os
import subprocess as subprocess
from datetime import datetime, date
import yaml
import time
import csv

cid = ""
username = ""
password = ""
config_dict = dict()

#Initialize config file
def initialize_global_variables(config):
    if os.path.isfile(config) == False:
        print("Error: Cannot find submission config at: " + config, file=sys.stderr)
    else:
        with open(config, 'r') as f:
            global config_dict
            config_dict = yaml.safe_load(f)
        if isinstance(config_dict, dict) == False:
            print("Config Error: Config file structure is incorrect.", file=sys.stderr)
            sys.exit()
        #Assign global values
        global cid
        cid = config_dict["gisaid"]["cid"]
        global username
        username = config_dict["gisaid"]["username"]
        global password
        password = config_dict["gisaid"]["password"]

#Checks authentication token from gisaid log to see if it has reached it's 100 day lifespan
#If lifespan has been reached it authenticates and then continues preprocessing
def check_authentication_date():
    #Check if uploader log exists]
    if os.path.isfile(os.path.join(os.path.dirname(os.path.abspath(__file__)), "gisaid_uploader.log")):
        #Check authentication date
        with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "gisaid_uploader.log"), "r") as f:
            line = f.readline().strip().split(": ")[1]
        auth_time = datetime.strptime(line, '%a %b %d %H:%M:%S %Y')
    else:
        print("gisaid_uploader.log missing. Reauthentication is required.")
        print("Run this command to authenticate: python " + os.path.join(os.path.dirname(os.path.abspath(__file__)), "gisaid_uploader.log") + " COV authenticate --cid " + cid)
        sys.exit()
    # If authentication has expired it will reauthenticate automatically
    if auth_time.date() <= datetime.today().date():
        print("Authentication token needs updating.")
        print("Run this command to authenticate: python " + os.path.join(os.path.dirname(os.path.abspath(__file__)), "gisaid_uploader.log") + " COV authenticate --cid " + cid)
        sys.exit()
    else:
        print("Authenticated")

#Run gisaid upload script and saves output to submission location
def run_uploader(unique_name, config, test):
    initialize_global_variables(config)
    print(f"\tSubmitting to GISAID\n")
    #Run gisaid_uploader.py and submit to gisaid.
    #try submission two times before erroring out
    attempts = 1
    complete = False
    error_holder = []
    while attempts < 3 and complete == False:
        proc = subprocess.run("python " + os.path.join(os.path.dirname(os.path.abspath(__file__)), "gisaid_uploader.py") + " --debug -l " +
            os.path.join(config_dict["general"]["submission_directory"], unique_name, "gisaid", unique_name + ".log") + " COV upload --fasta " +
            os.path.join(config_dict["general"]["submission_directory"], unique_name, "gisaid", unique_name + "_gisaid.fsa") + " --csv " +
            os.path.join(config_dict["general"]["submission_directory"], unique_name, "gisaid", unique_name + "_gisaid.csv") + " --failedout " +
            os.path.join(config_dict["general"]["submission_directory"], unique_name, "gisaid", unique_name + "_failed_meta.csv"),
            env = os.environ.copy(), stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True, shell=True)
        #print(proc.args)
        if proc.returncode != 0:
            error_holder.append(f"\t\t{proc.stderr}\n")
            attempts += 1
        else:
            complete = True
    
    if attempts == 3:
        print(f"\t\tGISAID Submission Unsuccessful After {attempts-1} Attempts")
    else:
        print(f"\t\tAfter {attempts-1} GISAID Submission Attempts, Submission Was Successful\n")
    
    if len(error_holder) != 0:
        print(f"\t\tErrors From Unsuccessful Attempts:\n")
        for error in set(error_holder):
            for line in error.split('\n'):
                print(f"\t\t{line}")

    if complete == True:
        print(f"\t\tWaiting for File to Write\n")
        #Wait until completion log written
        while not os.path.exists(os.path.join(config_dict["general"]["submission_directory"], unique_name, "gisaid", unique_name + ".log")):
            time.sleep(10)
    else:
        print(f"\t\tSubmission Errored Out\n")
