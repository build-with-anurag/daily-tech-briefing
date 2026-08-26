# Daily Tech Briefing → Google Drive

Fetches the day's top tech news, has Gemini curate and summarize it, and creates a formatted Google Doc in your Google Drive folder — automatically, every day at **8:00 AM IST**, via GitHub Actions.

---

## 🚀 GitHub Repo Setup

### 1. Push this project to GitHub
```bash
git init
git add .
git commit -m "Daily Tech Briefing Automation"
git remote add origin https://github.com/<your-username>/<repo-name>.git
git push -u origin main
```

---

### 2. Add Secrets to GitHub Repo
Go to: **Settings → Secrets and variables → Actions → New repository secret**

Add these 3 secrets:

| Secret Name | Value |
|---|---|
| `NEWS_API_KEY` | `YOUR_NEWS_API_KEY_HERE` |
| `GEMINI_API_KEY` | `YOUR_GEMINI_API_KEY_HERE` |
| `DRIVE_WEBHOOK_URL` | `YOUR_DRIVE_WEBHOOK_URL_HERE` |

---

### 3. Test Run
1. Go to the **Actions** tab in your GitHub repository.
2. Select **"Daily Tech Briefing"** on the left.
3. Click **"Run workflow"** → **Run workflow**.
4. Check your Google Drive folder: a new Google Doc will be created! 🎉
