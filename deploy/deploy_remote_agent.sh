#!/bin/bash
# Exit immediately if any command exits with a non-zero status
set -e

echo "================================================================="
echo "  Deploying/Updating Remote Agent on Vertex AI Agent Engine..."
echo "================================================================="
uv run python deploy/deploy_remote_agent.py

echo ""
echo "================================================================="
echo "  Deployment Completed successfully! 🎉"
echo "================================================================="
