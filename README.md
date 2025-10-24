# 💬 Chatbot template & Infor Skyline CRM backend

This repository now bundles two reference applications:

1. A simple Streamlit chatbot showcasing how to build conversational apps with OpenAI's GPT models.
2. A FastAPI-based CRM backend that integrates with Infor Skyline (SyteLine) to manage clients, opportunities, sales-date updates and daily invoice synchronisation.

[![Open in Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://chatbot-template.streamlit.app/)

### How to run it on your own machine

1. Install the requirements

   ```
   $ pip install -r requirements.txt
   ```

2. Run the app

   ```
   $ streamlit run streamlit_app.py
   ```

## Running the CRM backend

1. Install the requirements (same as above if you have not already).
2. Launch the FastAPI server:

   ```
   $ uvicorn main:app --reload
   ```

   The API will be available at `http://localhost:8000`. Interactive documentation is served at `/docs`.

3. (Optional) Start the daily invoice synchroniser in your application bootstrap by instantiating `crm.sync.SyncManager` and calling `schedule_daily_invoice_sync()`.
