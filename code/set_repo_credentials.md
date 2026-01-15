# Set Repo Credentials

This guide helps you connect local Git projects to the correct GitHub accounts when using multiple accounts on the same machine.

---

## Step 1 — Navigate to your repo
Open PowerShell and go to your project folder:

```powershell
cd C:\Path\To\Your\Repo
```

---

## Step 2 — Set the correct remote

### Personal repo (`abdullah-azi`)
```powershell
git remote set-url origin git@github-personal:abdullah-azi/RepoName.git
```

### Work repo (`SerenitysSlave`)
```powershell
git remote set-url origin git@github-second:SerenitysSlave/RepoName.git
```

Verify with:
```powershell
git remote -v
```

Expected output:

- Personal:
```
origin  git@github-personal:abdullah-azi/RepoName.git (fetch)
origin  git@github-personal:abdullah-azi/RepoName.git (push)
```
- Work:
```
origin  git@github-second:SerenitysSlave/RepoName.git (fetch)
origin  git@github-second:SerenitysSlave/RepoName.git (push)
```

---

## Step 3 — Set the local Git identity for commits

### Personal repo
```powershell
git config user.name "abdullah-azi"
git config user.email "syed.abdullahazi@gmail.com"
```

### Work repo
```powershell
git config user.name "SerenitysSlave"
git config user.email "i221186@nu.edu.pk"
```

> This ensures commits are attributed to the correct GitHub account.

---

## Step 4 — Test everything

1. Make a small test commit:
```powershell
echo "# Test commit" >> test.txt
git add test.txt
git commit -m "Test commit"
```

2. Push to the correct remote:
```powershell
git push origin main
```

- You should **not be prompted for a password** (SSH handles authentication).
- Commits will appear under the correct user on GitHub.

---

## Step 5 — Repeat for all repos

- Ensure each local project points to the correct SSH alias (`github-personal` or `github-second`).
- Ensure each local project has the correct `user.name` and `user.email` set.

This setup guarantees that your personal and work GitHub accounts can coexist on the same machine without conflicts.