# Mobile Access and Public Deployment

## A) Access on mobile in same Wi-Fi (fastest)

1. Open PowerShell on laptop.
2. Run:

```powershell
cd "C:\Users\monis\nptel-industrial-engineering-quiz"
python -m streamlit run quiz_app.py --server.address 0.0.0.0 --server.port 8501
```

3. In another terminal, get laptop IP:

```powershell
ipconfig
```

4. Open on mobile browser:

`http://<YOUR_LAPTOP_IPV4>:8501`

## B) Public website (recommended)

Use Streamlit Community Cloud.

### 1. Push project to GitHub

```powershell
cd "C:\Users\monis\nptel-industrial-engineering-quiz"
git add .
git commit -m "Set up NPTEL quiz app and question bank"
```

Create a new empty GitHub repository, then:

```powershell
git branch -M main
git remote add origin <YOUR_GITHUB_REPO_URL>
git push -u origin main
```

### 2. Deploy on Streamlit Cloud

1. Open [Streamlit Community Cloud](https://share.streamlit.io/).
2. Sign in with GitHub.
3. Click **New app**.
4. Select your repo and branch `main`.
5. Set main file path as `quiz_app.py`.
6. Deploy.

You will get a public URL you can open on phone anywhere.

## Notes

- Question bank file is `data/questions.json`.
- Week 12 answers are currently concept-verified and can be updated when official key is published.
