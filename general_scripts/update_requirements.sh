#!/bin/bash
# This script updates the requirements.txt file based on the current imports in the project.
# It uses pipreqs to scan the project directory and generate the requirements.txt file.
# The --force flag is used to overwrite the existing requirements.txt file.
pipreqs ./ --force
