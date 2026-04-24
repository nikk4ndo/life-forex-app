import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import google.generativeai as genai
from datetime import datetime
import os
import re

# --- 1. კონფიგურაცია ---
st.set_page_config(page_title="Life Forex AI", layout="wide")

# Gemini-ს გამართვა უსაფრთხოების ფილტრების გარეშე
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"], transport='rest')
    
    # უსაფრთხოების პარამეტრები (რომ არ დაბლოკოს პირადი ემოციები)
    safety_settings = [
        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
    ]
    
    model = genai.GenerativeModel(
        model_name='gemini-1.5-flash',
        safety_settings=safety_settings
    )
else:
    st.error("GEMINI_API_KEY ვერ მოიძებნა!")

DATA_FILE = "life_data.csv"

# --- 2. ფუნქციები ---

def load_data():
    if os.path.exists(DATA_FILE):
        try:
            df = pd.read_csv(DATA_FILE)
            df['Date'] = pd.to_datetime(df['Date'])
            return df
        except:
            return pd.DataFrame(columns=["Date", "Event", "Score", "Price"])
    return pd.DataFrame(columns=["Date", "Event", "Score", "Price"])

def analyze_with_gemini(txt):
    # უფრო "აგრესიული" ინსტრუქცია AI-ს
    prompt = f"""
    შენ ხარ ემოციური ფორექსის ტრეიდერი. 
    შეაფასე ეს მოვლენა მკაცრად -10-დან 10-მდე. 
    არ დაწერო ტექსტი, დააბრუნე მხოლოდ ერთი ციფრი.
    მოვლენა: {txt}
    """
    try:
        response = model.generate_content(prompt)
        # ვწმენდთ პასუხს ყველაფრისგან გარდა ციფრებისა
        res_text = response.text.strip()
        match = re.search(r"[-+]?\d*\.\d+|\d+", res_text)
        if match:
            return float(match.group())
        return 0.01 # თუ მაინც ვერ გაიგო, მცირე ქულა დავწეროთ
    except Exception as e:
        return 0.0

# --- 3. ინტერფეისი ---
st.title("📈 ჩემი ცხოვრების ფორექსი")

df = load_data()

with st.form("main_form", clear_on_submit=True):
    user_input = st.text_area("რა მოხდა დღეს?")
    submit = st.form_submit_button("ანალიზი და შენახვა")
    
    if submit and user_input:
        score = analyze_with_gemini(user_input)
        
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
        st.rerun()

# --- 4. ვიზუალიზაცია ---
if not df.empty:
    # ფერი ბოლო ცვლილების მიხედვით
    last_delta = df['Score'].iloc[-1]
    chart_color = '#00FF00' if last_delta > 0 else '#FF0000' if last_delta < 0 else '#FFFFFF'
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df['Date'], y=df['Price'], 
        mode='lines+markers',
        line=dict(color=chart_color, width=4),
        fill='tozeroy'
    ))
    fig.update_layout(template="plotly_dark", height=400)
    st.plotly_chart(fig, use_container_width=True)
    
    st.write("### 📝 ისტორია")
    st.dataframe(df.sort_values(by="Date", ascending=False), use_container_width=True)
