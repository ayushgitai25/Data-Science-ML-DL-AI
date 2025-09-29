---
title: CrewAI Multi-Agent News Research Tool
emoji: 🤖
colorFrom: blue
colorTo: purple
sdk: docker
sdk_version: "20.10.16"
app_port: 8501
pinned: false
license: mit
---

# 🤖 CrewAI Multi-Agent News Research Tool

Advanced AI collaboration system with FastAPI backend and Streamlit frontend.

## Architecture

- **FastAPI Backend** (Port 8000): API endpoints and CrewAI agents
- **Streamlit Frontend** (Port 8501): User interface  
- **Docker Deployment**: Both services in single container

## Configuration

Add these secrets for full functionality:
- `GOOGLE_API_KEY`: Google Gemini API key
- `NEWSDATA_API_KEY`: NewsData.io API key

## Usage

1. Enter research topic
2. Deploy AI agents
3. Monitor real-time collaboration
4. Download professional reports
