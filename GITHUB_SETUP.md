# GitHub Repository Setup Guide

Your local repository is ready! Follow these steps to push it to GitHub.

## Step 1: Create a GitHub Repository

1. Go to [GitHub.com](https://github.com) and sign in to your account (`abdullah-azi`)
2. Click the **"+"** icon in the top right corner
3. Select **"New repository"**
4. Fill in the repository details:
   - **Repository name**: `football-camera-switching` (or your preferred name)
   - **Description**: (optional) "Multi-camera football video switching and tracking system"
   - **Visibility**: Choose **Public** or **Private**
   - **DO NOT** initialize with README, .gitignore, or license (we already have these)
5. Click **"Create repository"**

## Step 2: Connect Your Local Repository to GitHub

After creating the repository, GitHub will show you setup instructions. Use the **SSH** option.

Run these commands in PowerShell (replace `RepoName` with your actual repository name):

### For Personal Account (abdullah-azi):
```powershell
cd "d:\New folder\football\final"
git remote add origin git@github-personal:abdullah-azi/RepoName.git
git branch -M main
git push -u origin main
```

### For Work Account (SerenitysSlave):
```powershell
cd "d:\New folder\football\final"
git remote add origin git@github-second:SerenitysSlave/RepoName.git
git config user.name "SerenitysSlave"
git config user.email "i221186@nu.edu.pk"
git branch -M main
git push -u origin main
```

## Step 3: Verify the Connection

After pushing, verify everything is set up correctly:

```powershell
git remote -v
```

You should see:
- For personal: `origin  git@github-personal:abdullah-azi/RepoName.git (fetch/push)`
- For work: `origin  git@github-second:SerenitysSlave/RepoName.git (fetch/push)`

## Current Git Configuration

Your repository is currently configured for:
- **User**: abdullah-azi
- **Email**: syed.abdullahazi@gmail.com
- **Branch**: main

If you need to switch to the work account, run:
```powershell
git config user.name "SerenitysSlave"
git config user.email "i221186@nu.edu.pk"
git remote set-url origin git@github-second:SerenitysSlave/RepoName.git
```

## Troubleshooting

- **SSH Key Issues**: Make sure your SSH keys are set up correctly for `github-personal` or `github-second` aliases
- **Permission Denied**: Verify you have push access to the repository
- **Repository Not Found**: Double-check the repository name and that it exists on GitHub
