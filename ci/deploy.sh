#!/usr/bin/env bash

if [[ $TRAVIS_BRANCH == "master" && $TRAVIS_PULL_REQUEST == false && $RUN_TESTS == true ]]
then
    echo -e "### Installing pip requirements to lib directory"
    pip install -t lib -r requirements.txt
    git clone https://github.com/dound/gae-sessions.git lib

    echo -e "\n### Deploying to App Engine"
    cd ./ci/google_appengine
    python appcfg.py update --oauth2_refresh_token=$AE_OAUTH_REFRESH ../../
fi
