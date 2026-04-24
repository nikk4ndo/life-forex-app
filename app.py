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
    st.error("Secrets-ში GEMINI_API_KEY ვერ მოიძებნა!")
else:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"], transport='rest')
    # ვიყენებთ უფრო სტაბილურ მოდელს
    model = genai.GenerativeModel('gemini-1.5-flash')

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
    # მკაცრი ინსტრუქცია AI-სთვის
    prompt = f"შეაფასე მოვლენის ემოციური გავლენა -10-დან +10-მდე. პასუხად დააბრუნე მხოლოდ ციფრი და სხვა არაფერი. მოვლენა: {txt}"
    try:
        response = model.generate_content(prompt)
        res_text = response.text.strip()
        # ვეძებთ ციფრს ტექსტში (მაგალითად თუ დაწერა "ქულაა: 5", ამოიღებს 5-ს)
        match = re.search(r"[-+]?\d*\.\d+|\d+", res_text)
        if match:
            return float(match.group())
        return 0.0
    except Exception as e:
        return 0.0

# --- 3. ინტერფეისი ---
st.title("📈 ჩემი ცხოვრების ფორექსი")

df = load_data()

with st.form("main_form", clear_on_submit=True):
    user_input = st.text_area("რა მოხდა?")
    submit = st.form_submit_button("ანალიზი და შენახვა")
    
    if submit and user_input:
        with st.spinner("AI აანალიზებს..."):
            score = analyze_with_gemini(user_input)
            
            # ფასის გამოთვლა (საწყისი ფასი 100)
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
            st.rerun()

# --- 4. ჩარტი და ისტორია ---
if not df.empty:
    # ფერი იცვლება ბოლო მოვლენის მიხედვით
    last_score = df['Score'].iloc[-1]
    color = "#00FF00" if last_score >= 0 else "#FF0000"
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df['Date'], 
        y=df['Price'], 
        mode='lines+markers',
        line=dict(color=color, width=3),
        fill='tozeroy'
    ))
    fig.update_layout(template="plotly_dark", title="ემოციური ინდექსი")
    st.plotly_chart(fig, use_container_width=True)
    
    st.write("### 📝 ისტორია")
    st.dataframe(df.sort_values(by="Date", ascending=False), use_container_width=True)
