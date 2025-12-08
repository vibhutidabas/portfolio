# Deployment Guide - Making Your Flask App Public

This guide will help you deploy your Flask application to make it publicly accessible. I recommend **Render.com** as it's free and beginner-friendly.

## Option 1: Deploy to Render.com (Recommended - Easiest)

### Step 1: Create a GitHub Repository
1. Go to [GitHub.com](https://github.com) and sign in (or create an account)
2. Click the "+" icon → "New repository"
3. Name it something like `resume-avatar-qa`
4. Make it **Public** (free Render requires public repos)
5. Click "Create repository"

### Step 2: Upload Your Code to GitHub
1. Open PowerShell/Command Prompt in your project folder (`resume_rag`)
2. Run these commands:
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git branch -M main
   git remote add origin https://github.com/YOUR_USERNAME/resume-avatar-qa.git
   git push -u origin main
   ```
   (Replace `YOUR_USERNAME` with your GitHub username)

### Step 3: Deploy on Render
1. Go to [render.com](https://render.com) and sign up (use GitHub to sign in - it's easier)
2. Click "New +" → "Web Service"
3. Connect your GitHub repository (`resume-avatar-qa`)
4. Configure the service:
   - **Name**: `resume-avatar-qa` (or any name you like)
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn local_qa_server_works_somewhat_4:app`
   - **Plan**: Select "Free" (or paid if you want)

5. **Add Environment Variables**:
   - Click "Advanced" → "Add Environment Variable"
   - Key: `GEMINI_API_KEY`
   - Value: `` (your API key)

6. Click "Create Web Service"
7. Wait 5-10 minutes for deployment
8. Your app will be live at: `https://resume-avatar-qa.onrender.com` (or similar)

### Step 4: Upload Your Files
Render needs your `resume.txt` and `avatar.glb` files. Make sure they're in your GitHub repo:
- ✅ `resume.txt` - Already in your repo
- ✅ `avatar.glb` - Already in your repo (if you're using it)

---

## Option 2: Deploy to Railway.app (Alternative)

1. Go to [railway.app](https://railway.app) and sign up with GitHub
2. Click "New Project" → "Deploy from GitHub repo"
3. Select your repository
4. Railway will auto-detect it's a Python app
5. Add environment variable: `GEMINI_API_KEY` = your API key
6. Deploy!

---

## Option 3: Quick Testing with ngrok (Temporary Public URL)

If you just want to test quickly without deploying:

1. Download ngrok from [ngrok.com](https://ngrok.com/download)
2. Extract and run:
   ```bash
   ngrok http 5000
   ```
3. ngrok will give you a public URL like `https://abc123.ngrok.io`
4. Share this URL (but it changes each time you restart ngrok)

**Note**: This is only for testing. For permanent hosting, use Render or Railway.

---

## Important Notes

### Security
- ✅ Your API key is now stored as an environment variable (safer)
- ⚠️ Make sure `resume.txt` doesn't contain sensitive info if your repo is public

### File Size Limits
- Render free tier: 100MB total
- Your `.glb` files might be large - if deployment fails, consider:
  - Compressing the model files
  - Using a CDN for model files
  - Upgrading to a paid plan

### Troubleshooting

**If deployment fails:**
1. Check the build logs in Render dashboard
2. Make sure `requirements.txt` has all dependencies
3. Ensure `resume.txt` exists in the repo

**If the app doesn't work:**
1. Check the service logs in Render
2. Verify environment variables are set correctly
3. Make sure the port is configured correctly (Render sets `PORT` automatically)

---

## After Deployment

Once deployed, you'll get a public URL like:
- `https://your-app-name.onrender.com`

Share this URL with anyone! The app will be accessible 24/7 (on free tier, it may sleep after inactivity but wakes up on first request).

---

## Need Help?

- Render Docs: https://render.com/docs
- Railway Docs: https://docs.railway.app
- Flask Deployment: https://flask.palletsprojects.com/en/latest/deploying/

