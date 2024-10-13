#!/bin/bash


# Setup
cd "${0%/*}"
BLENDER_EXE=$1

echo "Running tests using: $BLENDER_EXE"

STATUS=0
for FILEPATH in ./*.py; do
    echo "Test $FILEPATH"
    eval $BLENDER_EXE -b -noaudio --python "$FILEPATH"
    if [ $? -ne 0 ]; then
        # Track failed evaluation
        STATUS=1
    fi
done

echo ""
echo "-----------------"
if [ $STATUS -eq 0 ]; then
    echo "Success: All Passed!!!"
else
    echo "Test(s) Failed..."
fi
echo "-----------------"

# Terminate with failed status
exit $STATUS