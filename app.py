
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import google.generativeai as genai
from datetime import datetime
import os
import json
import re

# --- 1. კონფიგურაცია ---
st.set_page_config(page_title="Life Forex AI", layout="wide")

try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"], transport='rest')
    model = genai.GenerativeModel('models/gemini-1.5-flash')
except Exception as e:
    st.error("შეამოწმე Gemini API გასაღები Secrets-ში!")

DATA_FILE = "life_data.csv"

# --- 2. ფუნქციები ---

def load_data():
    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE)
        df['Date'] = pd.to_datetime(df['Date'])
        return df
    return pd.DataFrame(columns=["Date", "Event", "Score", "Price"])

def analyze_with_gemini(txt):
    # ვთხოვთ AI-ს ძალიან კონკრეტულ ფორმატს
    prompt = f"""
    გააანალიზე მოვლენა და შეაფასე -10-დან 10-მდე.
    დააბრუნე პასუხი მხოლოდ JSON ფორმატში, მაგალითად: {{"score": 5.5}}
    მოვლენა: {txt}
    """
    try:
        response = model.generate_content(prompt)
        # ვეძებთ ციფრს ნებისმიერი ფორმით, თუ JSON-მა დააგვიანა
        res_text = response.text
        numbers = re.findall(r"[-+]?\d*\.\d+|\d+", res_text)
        if numbers:
            return float(numbers[0])
        return 0.0
    except:
        return 0.0

# --- 3. ინტერფეისი ---
st.title("📈 ჩემი ცხოვრების ფორექსი")

df = load_data()

with st.form("main_form", clear_on_submit=True):
    user_input = st.text_area("რა მოხდა?")
    submit = st.form_submit_button("ანალიზი")
    
    if submit and user_input:
        with st.spinner("AI აანალიზებს..."):
            score = analyze_with_gemini(user_input)
            
            # ფასის ლოგიკა
            last_price = float(df['Price'].iloc[-1]) if not df.empty else 100.0
            new_price = last_price + score
            
            new_row = pd.DataFrame([{
                "Date": datetime.now(),
                "Event": user_input,
                "Score": score,
                "Price": new_price
            }])
            
            df = pd.concat([df, new_row], ignore_index=True)
            df.to_csv(DATA_FILE, index=False)
            st.success(f"ანალიზი დასრულდა: {score}")

# ჩარტი
if not df.empty:
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df['Date'], 
        y=df['Price'], 
        mode='lines+markers', 
        fill='tozeroy',
        line=dict(color='#00FF00' if score >= 0 else '#FF0000')
    ))
    fig.update_layout(template="plotly_dark", title="ემოციური ინდექსი")
    st.plotly_chart(fig, use_container_width=True)
    st.dataframe(df.sort_values(by="Date", ascending=False))
