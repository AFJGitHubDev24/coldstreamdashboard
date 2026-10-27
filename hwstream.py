
import streamlit as st

st.set_page_config(
    page_title="Hello World Dashboard",
    page_icon="👋",
    layout="centered"
)

st.title("Hello, World! 👋")
st.write("Welcome to my Streamlit dashboard running on AWS EC2.")

st.success("Your dashboard is working!")

if st.button("Click me"):
    st.balloons()
    st.write("Hello again!")
