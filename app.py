
import smtplib
from email.mime.text import MIMEText

import streamlit as st
from google import genai
from google.genai import types

from prompts import SYSTEM_PROMPT



# -----------------------------
# Secrets
# -----------------------------

GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
GMAIL_ADDRESS = st.secrets["GMAIL_ADDRESS"]
GMAIL_APP_PASSWORD = st.secrets["GMAIL_APP_PASSWORD"]


# Gemini Client

@st.cache_resource
def get_gemini_client():
    return genai.Client(api_key=GEMINI_API_KEY)


gemini_client = get_gemini_client()



# Send Email


def send_email(to_address, subject, body):

    message = MIMEText(body)

    message["Subject"] = subject
    message["From"] = GMAIL_ADDRESS
    message["To"] = to_address

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:

        server.login(
            GMAIL_ADDRESS,
            GMAIL_APP_PASSWORD
        )

        server.send_message(message)



# Onboarding


if "onboarded" not in st.session_state:

    st.title("🧾 SmartBill AI")

    st.caption(
        "Scan your receipt. Understand your expenses."
    )

    with st.form("onboarding_form"):

        name = st.text_input("Your name")

        email = st.text_input(
            "Email address"
        )

        submitted = st.form_submit_button(
            "Let's Start 🚀"
        )

        if submitted:

            if not name.strip() or not email.strip():

                st.warning(
                    "Please enter your name and email."
                )

            else:

                st.session_state.name = name.strip()

                st.session_state.email = email.strip()

                st.session_state.chat = (
                    gemini_client.chats.create(
                        model="gemini-3.5-flash",
                        config=types.GenerateContentConfig(
                            system_instruction=SYSTEM_PROMPT
                        )
                    )
                )

                st.session_state.messages = []

                st.session_state.onboarded = True

                st.rerun()

    st.stop()



# Main Application


st.title("🧾 SmartBill AI")

st.caption(
    f"Welcome, {st.session_state.name}! "
    "Upload your receipt below."
)



# Receipt Upload


uploaded_file = st.file_uploader(
    "Upload your receipt",
    type=["jpg", "jpeg", "png"]
)


if uploaded_file:

    image_bytes = uploaded_file.getvalue()

    st.image(
        image_bytes,
        caption="Uploaded Receipt",
        use_container_width=True
    )


    parts = [

        types.Part.from_bytes(
            data=image_bytes,
            mime_type=uploaded_file.type
        ),

        """
        Analyze this receipt.

        Give me:
        1. Item-wise expense breakdown
        2. Quantity if visible
        3. Price of each item
        4. Total amount
        5. Important observations

        Keep the response clear and easy to understand.
        """
    ]


    with st.spinner(
        "Reading your receipt..."
    ):

        response = (
            st.session_state.chat.send_message(parts)
        )


    st.subheader("📋 Expense Analysis")

    st.write(response.text)



    # Bill Split

    people = st.number_input(
        "Number of people",
        min_value=1,
        value=1,
        step=1
    )


    if people > 1:

        st.info(
            "The bill can be split equally "
            f"among {people} people."
        )


    # Email Summary

    email_body = f"""
Hello {st.session_state.name},

Here is your SmartBill AI receipt analysis:

{response.text}

Number of people: {people}

If the bill is split equally:

Each person pays approximately:
Total amount ÷ {people}

Regards,
SmartBill AI
"""


    if st.button("📧 Send Summary to My Email"):

        try:

            send_email(
                st.session_state.email,
                "SmartBill AI - Receipt Summary",
                email_body
            )

            st.success(
                "Receipt summary sent successfully! 📧"
            )

        except Exception as e:

            st.error(
                f"Email sending failed: {e}"
            )
