import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import google.generativeai as genai
from datetime import datetime
import os

# --- 1. ძირითადი პარამეტრები ---
st.set_page_config(page_title="Life Forex AI", layout="wide")

# Gemini-ს გამართვა (შესწორებული ვერსია)
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"], transport='rest')
    model = genai.GenerativeModel('models/gemini-1.5-flash')
except Exception as e:
    st.error("Secrets-ში გასაღები ვერ მოიძებნა ან არასწორია.")

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
    prompt = f"შეაფასე მოვლენის ემოციური გავლენა -10-დან +10-მდე. პასუხად დააბრუნე მხოლოდ ციფრი. მოვლენა: {txt}"
    try:
        response = model.generate_content(prompt)
        score_text = response.text.strip()
        # ვწმენდთ პასუხს ზედმეტი სიმბოლოებისგან
        clean_score = ''.join(c for c in score_text if c.isdigit() or c in '.-')
        return float(clean_score)
    except:
        return 0

# --- 3. ინტერფეისი ---

st.title("📈 ჩემი ცხოვრების ფორექსი")

df = load_data()

with st.form("my_form", clear_on_submit=True):
    user_input = st.text_area("რა მოხდა დღეს?")
    submit = st.form_submit_button("ანალიზი და შენახვა")
    
    if submit and user_input:
        with st.spinner("AI ფიქრობს..."):
            score = analyze_with_gemini(user_input)
            
            # ფასის გამოთვლა
            last_price = df['Price'].iloc[-1] if not df.empty else 100
            new_price = last_price + score
            
            # ახალი მონაცემი
            new_data = pd.DataFrame([{
                "Date": datetime.now(),
                "Event": user_input,
                "Score": score,
                "Price": new_price
            }])
            
            df = pd.concat([df, new_data], ignore_index=True)
            df.to_csv(DATA_FILE, index=False)
            st.success(f"მზადაა! ქულა: {score}")

# ჩარტის ჩვენება
if not df.empty:
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df['Date'], y=df['Price'], mode='lines+markers', fill='tozeroy'))
    fig.update_layout(template="plotly_dark", title="ემოციური დინამიკა")
    st.plotly_chart(fig, use_container_width=True)
    
    st.write("### ისტორია")
    st.dataframe(df.sort_values(by="Date", ascending=False), use_container_width=True)
