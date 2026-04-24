import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import google.generativeai as genai
from datetime import datetime
import os
import re

# --- კონფიგურაცია ---
st.set_page_config(page_title="Life Forex AI", layout="wide")

# Gemini-ს გამართვა
if "GEMINI_API_KEY" not in st.secrets:
    st.error("Secrets-ში GEMINI_API_KEY ვერ მოიძებნა!")
else:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"], transport='rest')
    model = genai.GenerativeModel('gemini-1.5-flash')

DATA_FILE = "life_data.csv"

def load_data():
    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE)
        df['Date'] = pd.to_datetime(df['Date'])
        return df
    return pd.DataFrame(columns=["Date", "Event", "Score", "Price"])

def analyze_with_ai(txt):
    # მკაცრი ინსტრუქცია AI-სთვის
    prompt = f"შეაფასე ტექსტის ემოცია -10-დან 10-მდე. პასუხად დააბრუნე მხოლოდ ერთი ციფრი, მაგალითად '5' ან '-3'. ტექსტი: {txt}"
    try:
        response = model.generate_content(prompt)
        # ვიღებთ მხოლოდ ციფრებს პასუხიდან
        res_text = response.text.strip()
        found = re.findall(r"[-+]?\d*\.\d+|\d+", res_text)
        if found:
            return float(found[0])
        return 0.0
    except:
        return 0.0

# --- ინტერფეისი ---
st.title("📈 ჩემი ცხოვრების ფორექსი")

df = load_data()

with st.form("input_form", clear_on_submit=True):
    user_text = st.text_area("რა ხდება შენს თავს?")
    btn = st.form_submit_button("ანალიზი")
    
    if btn and user_text:
        with st.spinner("AI ფიქრობს..."):
            score = analyze_with_ai(user_text)
            
            # ფასის გამოთვლა
            last_price = float(df['Price'].iloc[-1]) if not df.empty else 100.0
            new_price = last_price + score
            
            # შენახვა
            new_row = pd.DataFrame([{
                "Date": datetime.now(),
                "Event": user_text,
                "Score": score,
                "Price": new_price
            }])
            df = pd.concat([df, new_row], ignore_index=True)
            df.to_csv(DATA_FILE, index=False)
            st.success(f"ანალიზი დასრულდა. ქულა: {score}")
            st.rerun()

# --- გრაფიკი ---
if not df.empty:
    # ფერი იცვლება იმის მიხედვით, ბოლო მოვლენა კარგი იყო თუ ცუდი
    last_score = df['Score'].iloc[-1]
    color = "#00FF00" if last_score >= 0 else "#FF0000"
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df['Date'], 
        y=df['Price'], 
        mode='lines+markers',
        line=dict(color=color, width=4),
        fill='tozeroy',
        fillcolor='rgba(0, 255, 0, 0.1)' if last_score >= 0 else 'rgba(255, 0, 0, 0.1)'
    ))
    
    fig.update_layout(template="plotly_dark", height=400, margin=dict(l=0, r=0, t=30, b=0))
    st.plotly_chart(fig, use_container_width=True)
    
    st.write("### ისტორია")
    st.dataframe(df.sort_values(by="Date", ascending=False), use_container_width=True)
