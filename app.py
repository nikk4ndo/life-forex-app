import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import google.generativeai as genai
from datetime import datetime
import os

# --- 1. ძირითადი პარამეტრები ---
st.set_page_config(page_title="Life Forex AI", layout="wide")

# Gemini-ს გამართვა
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
    # უფრო მკაფიო ინსტრუქცია AI-სთვის
    prompt = f"""
    შენ ხარ ემოციური ანალიტიკოსი. შეაფასე მოვლენა -10.0-დან +10.0-მდე შკალაზე. 
    -10 არის კატასტროფა, 0 ნეიტრალურია, +10 არის უდიდესი ბედნიერება.
    პასუხად დააბრუნე მხოლოდ ციფრი (მაგალითად: 4.5 ან -2.1).
    მოვლენა: {txt}
    """
    try:
        response = model.generate_content(prompt)
        text_resp = response.text.strip()
        # ვპოულობთ მხოლოდ ციფრებს და წერტილს
        clean_score = "".join(c for c in text_resp if c.isdigit() or c in ".-")
        return float(clean_score)
    except:
        return 0.0

# --- 3. ინტერფეისი ---

st.title("📈 ჩემი ცხოვრების ფორექსი")

df = load_data()

with st.form("my_form", clear_on_submit=True):
    user_input = st.text_area("რა მოხდა დღეს?")
    submit = st.form_submit_button("ანალიზი და შენახვა")
    
    if submit and user_input:
        with st.spinner("AI აანალიზებს ემოციას..."):
            score = analyze_with_gemini(user_input)
            
            # საწყისი ფასი არის 100
            if df.empty:
                new_price = 100.0 + score
            else:
                new_price = float(df['Price'].iloc[-1]) + score
            
            new_data = pd.DataFrame([{
                "Date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "Event": user_input,
                "Score": score,
                "Price": round(new_price, 2)
            }])
            
            df = pd.concat([df, new_data], ignore_index=True)
            df.to_csv(DATA_FILE, index=False)
            st.success(f"ანალიზი დასრულდა. გავლენა: {score}")

# ჩარტის ჩვენება
if not df.empty:
    # ფერი იცვლება ბოლო ქულის მიხედვით
    line_color = "green" if df['Score'].iloc[-1] >= 0 else "red"
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df['Date'], 
        y=df['Price'], 
        mode='lines+markers',
        line=dict(color=line_color, width=3),
        fill='tozeroy',
        name="ბალანსი"
    ))
    
    fig.update_layout(
        template="plotly_dark", 
        title="ცხოვრების ემოციური ტრაექტორია",
        yaxis=dict(autorange=True) # ჩარტი ავტომატურად მოერგება ციფრებს
    )
    st.plotly_chart(fig, use_container_width=True)
    
    st.write("### 📝 ისტორია")
    st.dataframe(df.sort_values(by="Date", ascending=False), use_container_width=True)
else:
    st.info("ჩაწერე პირველი მოვლენა ანალიზის დასაწყებად.")
