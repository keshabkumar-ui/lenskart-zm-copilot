# Deployment Guide

This document outlines the steps to run the ZM Copilot locally or deploy it to a production environment.

## 1. Get AWS Bedrock Credentials
- Navigate to your AWS Account → IAM Users → Your User → Security Credentials.
- Copy your **Access Key ID** and **Secret Key**.
- *Ensure your IAM user has the `bedrock:InvokeModel` permission for Claude 3.*

## 2. Setup Environment
Clone the repository and prepare your virtual environment:

```bash
git clone <repository_url>
cd zm-copilot
python -m venv venv

# Activate environment:
# On macOS/Linux:
source venv/bin/activate  
# On Windows:
.\venv\Scripts\activate  

# Install dependencies:
pip install -r requirements.txt
```

## 3. Configure `.env`
You must configure the AI inference profile to enable the reasoning engine.

```bash
cp .env.example .env
```

Open `.env` and configure your credentials and Bedrock model IDs:
```env
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
# The app uses the following model IDs by default:
BEDROCK_MODEL_ID_PRIMARY=apac.anthropic.claude-sonnet-4-20250514-v1:0
BEDROCK_MODEL_ID_FALLBACK=apac.anthropic.claude-sonnet-4-20250514-v1:0
```

## 4. Verify Setup
You can optionally run a quick python script to verify that Bedrock can be reached:
```bash
python -c "from engine import get_bedrock_client; print('✅ Bedrock connected' if get_bedrock_client() else '❌ Check credentials')"
```

## 5. Run Locally
```bash
streamlit run app.py
```
The application will launch at `http://localhost:8501`.

---

## ☁️ Streamlit Cloud Deployment
To deploy this on Streamlit Cloud:
1. Push this code to a public/private GitHub repository.
2. Go to [share.streamlit.io](https://share.streamlit.io/) and select **"Deploy an app"**.
3. Choose the repository and set the main file path to `app.py`.
4. Click on **"Advanced settings..."** before deploying.
5. Add your `.env` variables into the **Secrets** section:
    ```toml
    AWS_ACCESS_KEY_ID = "your_access_key"
    AWS_SECRET_ACCESS_KEY = "your_secret_key"
    BEDROCK_MODEL_ID_PRIMARY = "apac.anthropic.claude-sonnet-4-20250514-v1:0"
    BEDROCK_MODEL_ID_FALLBACK = "apac.anthropic.claude-sonnet-4-20250514-v1:0"
    ```
6. Click **Deploy**.

## Monitoring & Database
- The feedback mechanism tracks ZM preferences inside `zm_learning.db` (SQLite). For a large-scale deployment, this SQLite database should be replaced with a managed database like Postgres or DynamoDB.
