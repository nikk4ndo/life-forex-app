import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from openai import OpenAI
from datetime import datetime
import os

# --- ინიციალიზაცია ---
st.set_page_config(page_title="Life Forex AI", layout="wide")
client = OpenAI(api_key="") # <--- შენი გასაღები აქ!
DATA_FILE = "life_data.csv"

def load_data():
    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE)
        df['Date'] = pd.to_datetime(df['Date'])
        return df
    return pd.DataFrame(columns=["Date", "Event", "Score", "Price"])

def analyze_with_ai(text):
    response = client.chat.completions.create(
        model="gpt-4o-mini", # ყველაზე იაფი და სწრაფი მოდელი
        messages=[{"role": "system", "content": "Analyze the event. Return ONLY a number between -100 and 100 based on its impact on person's life growth. 0 is neutral."},
                  {"role": "user", "content": text}]
    )
    return int(response.choices[0].message.content.strip())

# --- ინტერფეისი ---
st.title("📈 ჩემი ცხოვრების ფორექსი")

with st.sidebar:
    st.header("ახალი ჩანაწერი")
    txt = st.text_area("რა მოხდა / რა იგეგმება?")
    date = st.date_input("თარიღი", datetime.now())
    if st.button("დამატება"):
        df = load_data()
        score = analyze_with_ai(txt)
        last_price = df['Price'].iloc[-1] if not df.empty else 1000
        new_row = pd.DataFrame([{"Date": date, "Event": txt, "Score": score, "Price": last_price + score}])
        df = pd.concat([df, new_row], ignore_index=True).sort_values('Date')
        df.to_csv(DATA_FILE, index=False)
        st.success("მონაცემი შენახულია!")

# --- გრაფიკი ---
df = load_data()
if not df.empty:
    # მომავალი და წარსული მოვლენების გარჩევა
    today = pd.Timestamp(datetime.now().date())
    df['Status'] = df['Date'].apply(lambda x: 'Realized' if x <= today else 'Forecast')
    
    fig = go.Figure()
    # წარსული (მყარი ხაზი)
    real = df[df['Status'] == 'Realized']
    fig.add_trace(go.Scatter(x=real['Date'], y=real['Price'], mode='lines+markers', name='Actual', line=dict(color='#00ff00')))
    
    # მომავალი (პუნქტიანი ხაზი)
    forecast = df[df['Date'] >= real['Date'].max()] if not real.empty else df
    fig.add_trace(go.Scatter(x=forecast['Date'], y=forecast['Price'], mode='lines', name='Forecast', line=dict(dash='dash', color='#ffff00')))

    fig.update_layout(template="plotly_dark", hovermode="x")
    st.plotly_chart(fig, use_container_width=True)
    st.table(df.sort_values('Date', ascending=False))
