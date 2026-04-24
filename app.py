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
    st.error("გთხოვთ დაამატოთ GEMINI_API_KEY Secrets-ში!")
else:
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
            return pd.DataFrame(columns=["Date", "Event", "Score", "Price"])
    return pd.DataFrame(columns=["Date", "Event", "Score", "Price"])

def analyze_with_gemini(txt):
    prompt = f"შეაფასე მოვლენის ემოციური გავლენა -10-დან +10-მდე. პასუხად დააბრუნე მხოლოდ ციფრი. მოვლენა: {txt}"
    try:
        response = model.generate_content(prompt)
        # ვიყენებთ Regex-ს რომ მხოლოდ ციფრი ამოვიღოთ ტექსტიდან
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

# ფორმა მოვლენის ჩასაწერად
with st.form("main_form", clear_on_submit=True):
    user_input = st.text_area("რა მოხდა?")
    submit = st.form_submit_button("ანალიზი და შენახვა")
    
    if submit and user_input:
        with st.spinner("AI აანალიზებს..."):
            current_score = analyze_with_gemini(user_input)
            
            # ფასის გამოთვლა: ბოლო ფასს ვუმატებთ ახალ ქულას
            last_price = float(df['Price'].iloc[-1]) if not df.empty else 100.0
            new_price = last_price + current_score
            
            # ახალი ხაზის შექმნა
            new_row = pd.DataFrame([{
                "Date": datetime.now(),
                "Event": user_input,
                "Score": current_score,
                "Price": new_price
            }])
            
            # მონაცემების განახლება და შენახვა
            df = pd.concat([df, new_row], ignore_index=True)
            df.to_csv(DATA_FILE, index=False)
            st.success(f"მზადაა! ემოციური გავლენა: {current_score}")
            st.rerun() # აპლიკაციის თავიდან გაშვება მონაცემების საჩვენებლად

# --- 4. ვიზუალიზაცია ---
if not df.empty:
    # ვადგენთ ჩარტის ფერს ბოლო ქულის მიხედვით
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
    
    fig.update_layout(
        template="plotly_dark", 
        title="ემოციური ინდექსის დინამიკა",
        xaxis_title="დრო",
        yaxis_title="ქულა"
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    st.write("### 📝 ისტორია")
    # ვაჩვენებთ ისტორიას, ახალი მოვლენები ზემოთ
    st.dataframe(df.sort_values(by="Date", ascending=False), use_container_width=True)
else:
    st.info("ჩაწერე შენი პირველი მოვლენა ზემოთ მოცემულ ველში.")
