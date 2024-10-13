#!/bin/bash


# Setup
cd "${0%/*}"
BLENDER_EXE=$1

echo "Running tests in: $BLENDER_EXE"

STATUS=0
for FILEPATH in ./*.py; do
    eval $BLENDER_EXE -b -noaudio --python "$FILEPATH"
    if [ $? -ne 0 ]; then
        # Track failed evaluation
        STATUS=1
    fi
done

if [ $STATUS -eq 0 ]; then
    echo "-----------------"
    echo "Success: All Passed!!!"
    echo "-----------------"
fi

# Terminate with failed status
exit $STATUS