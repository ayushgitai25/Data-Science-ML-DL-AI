import numpy as np
import streamlit as st
import tensorflow as tf
from tensorflow.keras.datasets import imdb
from tensorflow.keras.preprocessing import sequence
from tensorflow.keras.models import load_model

# Load trained model
model = load_model('simple_rnn_imdb.h5')
word_index = imdb.get_word_index()

# Preprocess text
def preprocess_text(text, max_len=500):
    words = text.lower().split()
    encoded_review = [word_index.get(word, 2) + 3 for word in words]
    padded_review = sequence.pad_sequences([encoded_review], maxlen=max_len)
    return padded_review

# Predict sentiment
def predict_sentiment(review):
    processed_input = preprocess_text(review)
    prediction = model.predict(processed_input, verbose=0)
    score = prediction[0][0]
    sentiment = "Positive 😀" if score > 0.5 else "Negative 😞"
    return sentiment, score

# Streamlit UI
st.set_page_config(page_title="IMDB Sentiment Analyzer", page_icon="🎬", layout="centered")

st.title("🎬 IMDB Sentiment Analyzer")
st.write("Enter a movie review and find out if it's Positive or Negative!")

# Text input box
review = st.text_area("✍️ Write your review here:", "", height=150)

# Button
if st.button("🔍 Analyze Sentiment"):
    if review.strip() == "":
        st.warning("⚠️ Please enter a review before analyzing.")
    else:
        sentiment, score = predict_sentiment(review)

        # Unified colored answer box
        if sentiment.startswith("Positive"):
            st.markdown(
                f"""
                <div style='background-color:#d4edda;padding:20px;border-radius:12px;'>
                    <h4>😊 This review is Positive!</h4>
                    <p><b>Sentiment:</b> {sentiment}</p>
                    <p><b>Confidence:</b> {score*100:.2f}%</p>
                </div>
                """, unsafe_allow_html=True
            )
        else:
            st.markdown(
                f"""
                <div style='background-color:#f8d7da;padding:20px;border-radius:12px;'>
                    <h4>😞 This review is Negative.</h4>
                    <p><b>Sentiment:</b> {sentiment}</p>
                    <p><b>Confidence:</b> {score*100:.2f}%</p>
                </div>
                """, unsafe_allow_html=True
            )
