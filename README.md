# Data Science - ML - DL - AI

## Steps to push files in the repo:

- cd \dir
- git init
- git add .
- git commit -m "Initial commit"
- git remote add origin https://github.com/ayushgitai25/Data-Science-ML-DL-AI.git
- git branch -M main
- git push -u origin main

### git push -u origin main : It tells Git:
#### "Hey, from now on, my local branch main should track the remote branch main on origin."

## On Google Colab:
- git config --global user.email "you@example.com"
- git config --global user.name "Your Name"
### All steps remain the same, just you may need to use a token(classic) and the use it like:
- Go to GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic).

- Click “Generate new token (classic)” → select scopes: repo, workflow, read:org.

- Copy the generated token.

- Then push using:
  
  - git remote set-url origin https://**TOKEN**@github.com/ayushgitai25/Data-Science-ML-DL-AI.git
  - git push -u origin main
