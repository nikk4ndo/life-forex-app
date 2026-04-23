import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import google.generativeai as genai
from datetime import datetime
import os

# --- ინიციალიზაცია ---
st.set_page_config(page_title="Life Forex AI", layout="wide")

# Gemini-ს კონფიგურაცია Secrets-დან
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    model = genai.GenerativeModel('gemini-1.5-flash')
except Exception as e:
    st.error("Gemini API გასაღები ვერ მოიძებნა. შეამოწმე Secrets!")

DATA_FILE = "life_data.csv"

# მონაცემების ჩატვირთვის ფუნქცია
def load_data():
    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE)
        df['Date'] = pd.to_datetime(df['Date'])
        return df
    return pd.DataFrame(columns=["Date", "Event", "Score", "Price"])

# AI ანალიზის ფუნქცია (Gemini)
def analyze_with_gemini(txt):
    prompt = f"""
    შენ ხარ ემოციური ანალიტიკოსი. გააანალიზე შემდეგი მოვლენა და შეაფასე მისი ემოციური გავლენა 
    ავტორის ცხოვრებაზე -10-დან (ძალიან ნეგატიური) +10-მდე (ძალიან პოზიტიური).
    პასუხად დააბრუნე მხოლოდ და მხოლოდ ერთი ციფრი (მაგალითად: 5 ან -3.5).
    მოვლენა: {txt}
    """
    try:
        response = model.generate_content(prompt)
        # ამოვიღოთ ტექსტური პასუხი და ვაქციოთ ციფრად
        score_text = response.text.strip()
        return float(''.join(c for c in score_text if c.isdigit() or c in '.-'))
    except Exception as e:
        st.warning(f"AI ანალიზი ვერ მოხერხდა: {e}")
        return 0

# --- ინტერფეისი ---
st.title("📈 ჩემი ცხოვრების ფორექსი")
st.subheader("მართე შენი ცხოვრების ემოციური ტრაექტორია")

df = load_data()

# ახალი მოვლენის დამატება
with st.form("event_form", clear_on_submit=True):
    txt = st.text_area("რა მოხდა დღეს?")
    submitted = st.form_submit_button("ანალიზი და შენახვა")
    
    if submitted and txt:
        with st.spinner("AI აანალიზებს მოვლენას..."):
            score = analyze_with_gemini(txt)
            
            # ფასის სიმულაცია (წინა ფასს ვუმატებთ ახალ ქულას)
            last_price = df['Price'].iloc[-1] if not df.empty else 100
            new_price = last_price + score
            
            # ახალი მონაცემის დამატება
            new_row = {
                "Date": datetime.now(),
                "Event": txt,
                "Score": score,
                "Price": new_price
            }
            
            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
            df.to_csv(DATA_FILE, index=False)
            st.success(f"მოვლენა შენახულია! ქულა: {score}")

# ჩარტის აგება
if not df.empty:
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df['Date'], 
        y=df['Price'],
        mode='lines+markers',
        line=dict(color='#00ff00' if df['Score'].iloc[-1] >= 0 else '#ff0000', width=3),
        fill='tozeroy',
        name="ბედნიერების ინდექსი"
    ))
    
    fig.update_layout(
        title="ემოციური ბალანსის დინამიკა",
        xaxis_title="დრო",
        yaxis_title="ინდექსი",
        template="plotly_dark",
        height=500
    )
    
    st.plotly_chart(fig, use_container_width=True)

    # ისტორიის ჩვენება
    st.write("### 📝 ბოლო მოვლენები")
    st.dataframe(df.sort_values(by="Date", ascending=False)[["Date", "Event", "Score"]], use_container_width=True)
else:
    st.info("ჯერჯერობით მონაცემები არ არის. ჩაწერე შენი პირველი მოვლენა!")
