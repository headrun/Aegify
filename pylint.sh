#!/bin/sh

set +x

find * -name '*.py' | xargs pylint -E --generated-members=objects
