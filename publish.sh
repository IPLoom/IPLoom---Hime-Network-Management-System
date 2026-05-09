#!/bin/bash

# IPLoom Docker Publishing Script
# This script automates the build and push process for the monolithic IPLoom image.

# Set your Docker Hub username here or pass as an argument
DOCKER_USER=${1:-"wglabz"}
IMAGE_NAME="iploom"

# Read and increment version
VERSION_FILE="VERSION"
if [ ! -f "$VERSION_FILE" ]; then
    echo "0.3.1" > "$VERSION_FILE"
fi

CURRENT_VERSION=$(cat "$VERSION_FILE")
# Increment patch version (very simple increment)
BASE_VERSION=$(echo $CURRENT_VERSION | cut -d. -f1-2)
PATCH=$(echo $CURRENT_VERSION | cut -d. -f3)
NEW_PATCH=$((PATCH + 1))
NEW_VERSION="$BASE_VERSION.$NEW_PATCH"

echo "📈 Incrementing version: $CURRENT_VERSION -> $NEW_VERSION"
echo "$NEW_VERSION" > "$VERSION_FILE"

FULL_TAG="$DOCKER_USER/$IMAGE_NAME:$NEW_VERSION"

echo "📦 Starting UI Build..."
cd ui
# Inject version into Vite build if needed (simplest way is env var)
VITE_APP_VERSION="v$NEW_VERSION" npm run build
cd ..

echo "🚀 Starting Docker build for $FULL_TAG..."

# Build the monolithic image from the root directory using Buildx for ARM64
echo "🔨 Building for platform linux/arm64..."
if docker buildx build --platform linux/arm64 -t "$FULL_TAG" -t "$DOCKER_USER/$IMAGE_NAME:latest" --load .; then
    echo "✅ Build successful!"
else
    echo "❌ Build failed. Please check the logs above."
    echo "💡 Hint: Ensure you have a buildx builder instance: 'docker buildx create --use'"
    exit 1
fi

echo "📦 Image tagged as $FULL_TAG"

# Optional: Push to Docker Hub
read -p "❓ Do you want to push this image to docker.io? (y/N): " confirm
if [[ $confirm == [yY] || $confirm == [yY][eE][sS] ]]; then
    echo "🔑 Ensuring you are logged in..."
    docker login
    
    echo "📤 Pushing $FULL_TAG to Docker Hub..."
    if docker push "$FULL_TAG"; then
        echo "🎉 Successfully published to https://hub.docker.com/r/$DOCKER_USER/$IMAGE_NAME"
    else
        echo "❌ Push failed. Are you logged in to Docker Hub?"
        exit 1
    fi
else
    echo "⏭️ Push skipped. You can push manually using: docker push $FULL_TAG"
fi
