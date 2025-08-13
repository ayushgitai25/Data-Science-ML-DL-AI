import streamlit as st
import numpy as np
import tensorflow as tf
from tensorflow.keras.models import load_model
from sklearn.preprocessing import StandardScaler, LabelEncoder, OneHotEncoder
import pandas as pd
import pickle

# Load the trained model and preprocessing objects
model = load_model('model.h5')

with open('one_hot_encoder.pkl', 'rb') as file:
    one_hot_encoder = pickle.load(file)

with open('label_encoder_gender.pkl', 'rb') as file:
    label_encoder_gender = pickle.load(file)

with open('scaler.pkl', 'rb') as file:
    scaler = pickle.load(file)

st.title('Customer Churn Prediction')

# Select boxes for categorical data
geography = st.selectbox("Geography", one_hot_encoder.categories_[0])
gender = st.selectbox("Gender", label_encoder_gender.classes_)
has_cr_card = st.selectbox("Has Credit Card", [0, 1])
is_active_member = st.selectbox("Is Active Member", [0, 1])

# Numeric inputs
credit_score = st.number_input("Credit Score")
age = st.number_input("Age", min_value=18, max_value=100)
balance = st.number_input("Balance")
estimated_salary = st.number_input("Estimated Salary")
tenure = st.slider("Tenure (years)", min_value=0, max_value=10)

# Slider for number of products
num_of_products = st.slider("Number of Products", min_value=1, max_value=4)

# Create DataFrame with values in lists
input_df = pd.DataFrame({
    "CreditScore": [credit_score],
    "Geography": [geography],
    "Gender": [gender],
    "Age": [age],
    "Tenure": [tenure],
    "Balance": [balance],
    "NumOfProducts": [num_of_products],
    "HasCrCard": [has_cr_card],
    "IsActiveMember": [is_active_member],
    "EstimatedSalary": [estimated_salary],
})

# Button to make prediction
if st.button("Predict Churn"):
    # Encode Geography
    geo_encoded = one_hot_encoder.transform([input_df['Geography']])
    geo_encoded_df = pd.DataFrame(
        geo_encoded,
        columns=one_hot_encoder.get_feature_names_out(['Geography'])
    )
 
    # Encode Gender
    input_df['Gender'] = label_encoder_gender.transform(input_df['Gender'])

    # Combine encoded columns
    input_df = pd.concat([input_df.drop('Geography', axis=1), geo_encoded_df], axis=1)

    # Scale features
    input_df_scaled = scaler.transform(input_df)

    # Predict
    prediction_prob = model.predict(input_df_scaled)[0][0]
    exited = int(prediction_prob > 0.5)

    # Display output
    st.subheader("Prediction Result")
    if exited:
        st.error(f"🚨 Customer likely to EXIT the bank. Probability: {prediction_prob}")
    else:
        st.success(f"✅ Customer likely to STAY with the bank. Probability: {prediction_prob}")
