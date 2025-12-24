param (
    [string]$InputFolder
)

# Build Docker image if it doesn't exist
if (-not (docker image inspect wildlife-test -ErrorAction SilentlyContinue)) {
    docker build -t wildlife-test .
}

# Create temp directory
$TempDir = "$env:USERPROFILE\trailcams_output\temp"
New-Item -ItemType Directory -Force -Path $TempDir | Out-Null

# Copy images to temp directory
Get-ChildItem -Path $InputFolder -Recurse -Include *.jpg, *.jpeg, *.png | ForEach-Object {
    Copy-Item $_.FullName -Destination $TempDir
}

# Run Docker container
docker run --rm -v "$env:USERPROFILE\trailcams_output:/working_volume" wildlife-test

# Clean up temp directory
Remove-Item "$TempDir\*" -Force