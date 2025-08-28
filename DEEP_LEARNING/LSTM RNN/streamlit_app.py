import streamlit as st
import numpy as np
import pickle
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing.sequence import pad_sequences

# -------------------------------
# Load model and tokenizer
# -------------------------------
@st.cache_resource
def load_lstm_model():
    return load_model("lstm_rnn_hamlet.h5")

@st.cache_resource
def load_tokenizer():
    with open("tokenizer.pickle", "rb") as handle:
        return pickle.load(handle)

model = load_lstm_model()
tokenizer = load_tokenizer()

# -------------------------------
# App title
# -------------------------------
st.title("📜 Shakespeare Next Word Predictor")
st.write("Trained on *Hamlet* by William Shakespeare")

# -------------------------------
# Define helper function
# -------------------------------
total_words = len(tokenizer.word_index) + 1
max_sequence_len = 14  # <-- must match training value

def predict_next_word(seed_text):
    """Predict next n words for a given seed text."""
  
    token_list = tokenizer.texts_to_sequences([seed_text])[0]
    token_list = pad_sequences([token_list], maxlen=max_sequence_len-1, padding="pre")

    predicted_probs = model.predict(token_list, verbose=0)
    predicted_index = np.argmax(predicted_probs, axis=1)[0]

    for word, index in tokenizer.word_index.items():
        if index == predicted_index:
            seed_text += " " + word
            break
    return seed_text

# -------------------------------
# User input
# -------------------------------
seed_text = st.text_input("✍️ Enter a starting phrase:", "to be or not")

if st.button("Generate"):
    result = predict_next_word(seed_text)
    st.markdown("### ✅ Generated Text:")
    st.success(result)

# -------------------------------
# Footer
# -------------------------------
st.caption("⚡ Powered by TensorFlow + Streamlit")
