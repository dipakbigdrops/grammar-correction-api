#!/bin/bash

# Docker Build Script for Grammar Correction API

echo "🐳 Building Grammar Correction API Docker Image..."
echo ""

# Build the image
docker build -t grammar-correction-api:latest .

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Docker image built successfully!"
    echo ""
    echo "To run the container:"
    echo "  docker run -d --name grammar-api -p 8000:8000 grammar-correction-api:latest"
    echo ""
    echo "Or use Docker Compose:"
    echo "  docker-compose up -d"
    echo ""
else
    echo ""
    echo "❌ Build failed! Check the error messages above."
    exit 1
fi

