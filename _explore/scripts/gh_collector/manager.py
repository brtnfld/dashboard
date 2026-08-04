from scraper.github import queryManager as qm
import os
from os import environ as env
import json
import requests
import sys
from urllib.parse import quote as urlquote




def manager(data_file: os.PathLike):
    """
    Initializes the data collector and reads input lists of organizations and independent repos of interest.
    Returns the dataCollector and cdash_mapping.
    """
    # Initialize data collector (single file for all repo types)
    dataCollector = qm.DataManager(data_file, False)
    dataCollector.data = {"data": {}}

    return dataCollector
