#!/bin/bash
# A script to archive resources from the python app and store them as static
# files for openshift cloud hosting.

workon monroe
python setup.py archive_tw2_resources -o ../static -d tg2app -f

mkdir -p ../static/resources/tg2app.widgets
cp -rf tg2app/public ../static/resources/tg2app.widgets/.
