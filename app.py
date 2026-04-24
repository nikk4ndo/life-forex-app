import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import google.generativeai as genai
from datetime import datetime
import os
import re

# --- 1. კონფიგურაცია ---
st.set_page_config(page_title="Life Forex AI", layout="wide")

if "GEMINI_API_KEY" not in st.secrets:
    st.error("🔑 Secrets-ში GEMINI_API_KEY არ არის ჩაწერილი სწორად!")
    st.stop()

try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"], transport='rest')
    model = genai.GenerativeModel('models/gemini-1.5-flash')
except Exception as e:
    st.error(f"კონფიგურაციის შეცდომა: {e}")

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
    prompt = f"შეაფასე ამ მოვლენის ემოციური გავლენა -10-დან +10-მდე. პასუხად დაწერე მხოლოდ რიცხვი. მოვლენა: {txt}"
    try:
        response = model.generate_content(prompt)
        
        # --- დებაგინგი: ეკრანზე გამოგვაქვს AI-ს ნამდვილი პასუხი ---
        st.info(f"🤖 AI-ს ზუსტი პასუხი: {response.text}")
        
        match = re.search(r"[-+]?\d*\.\d+|\d+", response.text)
        if match:
            return float(match.group())
        return 0.0
    except Exception as e:
        # --- დებაგინგი: ეკრანზე გამოგვაქვს ფარული შეცდომა ---
        st.error(f"❌ შეცდომა AI-სთან კავშირისას: {e}")
        return 0.0

# --- 3. ინტერფეისი ---
st.title("📈 ჩემი ცხოვრების ფორექსი")

df = load_data()

with st.form("main_form", clear_on_submit=False):
    user_input = st.text_area("რა მოხდა?")
    submit = st.form_submit_button("ანალიზი და შენახვა")
    
    if submit and user_input:
        with st.spinner("AI ფიქრობს..."):
            current_score = analyze_with_gemini(user_input)
            
            last_price = float(df['Price'].iloc[-1]) if not df.empty else 100.0
            new_price = last_price + current_score
            
            new_row = pd.DataFrame([{
                "Date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "Event": user_input,
                "Score": current_score,
                "Price": round(new_price, 2)
            }])
            
            df = pd.concat([df, new_row], ignore_index=True)
            df.to_csv(DATA_FILE, index=False)
            
            st.success(f"მზადაა! გავლენა: {current_score}")

# --- 4. ვიზუალიზაცია ---
if not df.empty:
    last_score = df['Score'].iloc[-1]
    chart_color = '#00FF00' if last_score >= 0 else '#FF0000'
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df['Date'], 
        y=df['Price'], 
        mode='lines+markers',
        line=dict(color=chart_color, width=3),
        fill='tozeroy',
        name="ბედნიერების ინდექსი"
    ))
    
    fig.update_layout(template="plotly_dark", title="ინდექსის დინამიკა")
    st.plotly_chart(fig, use_container_width=True)
    
    st.dataframe(df.sort_values(by="Date", ascending=False), use_container_width=True)
