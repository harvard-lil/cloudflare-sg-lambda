#!/bin/bash

pip install --target ./package -r requirements.txt
cd package/
zip -r ../deployment-package-`git rev-parse --short HEAD`.zip .
cd ..
zip -g deployment-package-`git rev-parse --short HEAD`.zip lambda_function.py
