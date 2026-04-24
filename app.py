
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
def init_gemini():
    if "GEMINI_API_KEY" not in st.secrets:
        st.error("🔑 Secrets-ში GEMINI_API_KEY არ არის!")
        return None
    try:
        genai.configure(api_key=st.secrets["GEMINI_API_KEY"], transport='rest')
        return genai.GenerativeModel('models/gemini-1.5-flash')
    except Exception as e:
        st.error(f"კონფიგურაციის შეცდომა: {e}")
        return None

model = init_gemini()
DATA_FILE = "life_data.csv"

# --- 2. ფუნქციები ---
def load_data():
    if os.path.exists(DATA_FILE):
        return pd.read_csv(DATA_FILE)
    return pd.DataFrame(columns=["Date", "Event", "Score", "Price"])

def analyze_with_gemini(txt):
    if model is None:
        return None, "AI მოდელი არ არის ინიციალიზებული"
    
    prompt = f"შეაფასე ემოციური გავლენა -10-დან +10-მდე. დააბრუნე მხოლოდ ციფრი. მოვლენა: {txt}"
    try:
        response = model.generate_content(prompt)
        # ვეძებთ ციფრს პასუხში
        match = re.search(r"[-+]?\d*\.\d+|\d+", response.text)
        if match:
            return float(match.group()), None
        return None, f"AI-მ ვერ დააბრუნა ციფრი. პასუხი იყო: {response.text}"
    except Exception as e:
        return None, str(e)

# --- 3. ინტერფეისი ---
st.title("📈 ჩემი ცხოვრების ფორექსი")

df = load_data()

# ვიყენებთ ჩვეულებრივ ღილაკს ფორმის ნაცვლად, რომ ერორი არ გაქრეს
user_input = st.text_area("რა მოხდა?")
if st.button("ანალიზი და შენახვა"):
    if user_input:
        with st.spinner("AI მუშაობს..."):
            score, error = analyze_with_gemini(user_input)
            
            if error:
                # აქ ჩერდება შეცდომა და არ ქრება!
                st.error(f"❌ დეტალური შეცდომა: {error}")
                st.info("შესაძლო მიზეზი: API გასაღები ახალია და ჯერ არ გააქტიურდა, ან ინტერნეტის ხარვეზია.")
            else:
                last_price = float(df['Price'].iloc[-1]) if not df.empty else 100.0
                new_price = last_price + score
                
                new_row = pd.DataFrame([{
                    "Date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "Event": user_input,
                    "Score": score,
                    "Price": round(new_price, 2)
                }])
                
                df = pd.concat([df, new_row], ignore_index=True)
                df.to_csv(DATA_FILE, index=False)
                st.success(f"შენახულია! ქულა: {score}")
                # მხოლოდ წარმატების შემთხვევაში ვაჩვენებთ განახლებულ მონაცემებს
    else:
        st.warning("გთხოვთ ჩაწეროთ ტექსტი")

# --- 4. ვიზუალიზაცია ---
if not df.empty:
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df['Date'], y=df['Price'], mode='lines+markers', fill='tozeroy'))
    fig.update_layout(template="plotly_dark", title="ემოციური ინდექსი")
    st.plotly_chart(fig, use_container_width=True)
    st.write("### ისტორია")
    st.dataframe(df.sort_values(by="Date", ascending=False), use_container_width=True)
