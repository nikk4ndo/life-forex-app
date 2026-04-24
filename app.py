import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import google.generativeai as genai
from datetime import datetime
import os
import re

# --- 1. კონფიგურაცია ---
st.set_page_config(page_title="Life Forex AI", layout="wide")

# Gemini-ს გამართვა
if "GEMINI_API_KEY" not in st.secrets:
    st.error("🔑 Secrets-ში GEMINI_API_KEY არ არის!")
    st.stop()

genai.configure(api_key=st.secrets["GEMINI_API_KEY"], transport='rest')
model = genai.GenerativeModel('models/gemini-1.5-flash')

DATA_FILE = "life_data.csv"

# --- 2. ფუნქციები ---
def load_data():
    if os.path.exists(DATA_FILE):
        try:
            df = pd.read_csv(DATA_FILE)
            df['Date'] = pd.to_datetime(df['Date'])
            return df
        except:
            pass
    return pd.DataFrame(columns=["Date", "Event", "Score", "Price"])

def analyze_with_gemini(txt):
    prompt = f"შეაფასე მოვლენის ემოციური გავლენა -10-დან +10-მდე. პასუხად დაწერე მხოლოდ ციფრი. მოვლენა: {txt}"
    try:
        response = model.generate_content(prompt)
        # ამოვიღოთ მხოლოდ ციფრი
        match = re.search(r"[-+]?\d*\.\d+|\d+", response.text)
        if match:
            return float(match.group())
        return 0.0
    except Exception as e:
        st.error(f"AI შეცდომა: {e}")
        return 0.0

# --- 3. ინტერფეისი ---
st.title("📈 ჩემი ცხოვრების ფორექსი")

df = load_data()

with st.form("main_form", clear_on_submit=True):
    user_input = st.text_area("რა მოხდა?")
    submit = st.form_submit_button("ანალიზი და შენახვა")
    
    if submit and user_input:
        with st.spinner("AI ფიქრობს..."):
            current_score = analyze_with_gemini(user_input)
            
            last_price = float(df['Price'].iloc[-1]) if not df.empty else 100.0
            new_price = last_price + current_score
            
            new_row = pd.DataFrame([{
                "Date": datetime.now(),
                "Event": user_input,
                "Score": current_score,
                "Price": round(new_price, 2)
            }])
            
            df = pd.concat([df, new_row], ignore_index=True)
            df.to_csv(DATA_FILE, index=False)
            st.success(f"მზადაა! გავლენა: {current_score}")
            st.rerun()

# --- 4. ვიზუალიზაცია (აქ იყო შეცდომა და გასწორდა) ---
if not df.empty:
    # ვიღებთ ბოლო ჩანაწერის ქულას DataFrame-დან
    last_entry_score = df['Score'].iloc[-1]
    chart_color = '#00FF00' if last_entry_score >= 0 else '#FF0000'
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df['Date'], 
        y=df['Price'], 
        mode='lines+markers',
        line=dict(color=chart_color, width=3),
        fill='tozeroy'
    ))
    
    fig.update_layout(template="plotly_dark", title="ემოციური ტრაექტორია")
    st.plotly_chart(fig, use_container_width=True)
    
    st.write("### ისტორია")
    st.dataframe(df.sort_values(by="Date", ascending=False), use_container_width=True)
