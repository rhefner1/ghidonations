#!/usr/bin/env bash

echo -e  "### Cleaning up"
rm -rf ./ci/google_appengine
echo "Removed google_appengine"
rm -f ./ci/appengine_sdk.zip
echo "Removed appengine_sdk.zip"
