#!/bin/bash

# Create a temporary directory
TEMP_DIR=`mktemp -d`

# Small workaround for MacOS users
cat >$TEMP_DIR/setup.cfg<<EOL
[install]
prefix=
EOL

# Install the dependencies
pip3 install -r requirements.txt -t $TEMP_DIR

# Add the actual code
cp signalfx_statuspage_integration.py $TEMP_DIR

# Finally let's bundle this
pushd $TEMP_DIR
zip -r signalfx_to_statuspage_integration.zip ./*
popd

# Copy the tmp file back to the dist directory so it can be uploaded
cp $TEMP_DIR/signalfx_to_statuspage_integration.zip dist/
