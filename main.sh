#!/bin/zsh
INPUT_FOLDER=$1

# Build Docker image if it doesn't exist
if ! docker image inspect wildlife-test >/dev/null 2>&1; then
    docker build -t wildlife-test .
fi


# Copy all images in INPUT_FOLDER to a temp directory
mkdir -p ~/trailcams_output/temp
find "$INPUT_FOLDER" -type f \( -iname '*.jpg' -o -iname '*.jpeg' -o -iname '*.png' \) -exec cp {} ~/trailcams_output/temp/ \;


docker run --rm -v ~/trailcams_output:/working_volume wildlife-test

rm ~/trailcams_output/temp/*