# AyurLink API - Deployment Guide

This API service can be deployed to the cloud so users can access it via URL.

## Quick Start

1. **Run the setup script**:
   ```bash
   python setup_deployment.py
   ```

2. **Read the comprehensive guide**:
   - See the detailed deployment guide in the artifacts
   - Choose your preferred platform (Render, Railway, Fly.io, or DigitalOcean)

3. **Push to GitHub**:
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin https://github.com/YOUR_USERNAME/ayurlink-api.git
   git push -u origin main
   ```

4. **Deploy**:
   - Follow platform-specific instructions in the deployment guide
   - Recommended for beginners: **Render** (free tier with PostgreSQL)

## Files Created for Deployment

- ✅ `requirements.txt` - Python dependencies
- ✅ `Procfile` - Start command for cloud platforms
- ✅ `.env.example` - Environment variable template
- ✅ `runtime.txt` - Python version specification
- ✅ `setup_deployment.py` - Deployment setup helper script

## Platform Recommendations

| Platform | Cost | Difficulty | Database Included |
|----------|------|------------|-------------------|
| Render | Free | ⭐ Easy | ✅ Yes |
| Railway | Free (limited) | ⭐ Easy | ✅ Yes |
| Fly.io | Free | ⭐⭐ Medium | ⚠️ Separate setup |
| DigitalOcean | $5-15/mo | ⭐⭐ Medium | ⚠️ Separate setup |

## Support

Refer to the comprehensive deployment guide for:
- Step-by-step deployment instructions
- Database setup
- Environment configuration
- Troubleshooting
- Testing and verification

Your API will be accessible at URLs like:
- `https://your-app.onrender.com` (Render)
- `https://your-app.up.railway.app` (Railway)
- `https://your-app.fly.dev` (Fly.io)
