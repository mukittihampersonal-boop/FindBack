
import streamlit as st
import pandas as pd
import os
from difflib import SequenceMatcher
from PIL import Image
import cv2
import numpy as np

st.set_page_config(page_title="FindBack", page_icon="🔍", layout="wide")

os.makedirs("uploads/lost", exist_ok=True)
os.makedirs("uploads/found", exist_ok=True)

if not os.path.exists("lost_reports.csv"):
    pd.DataFrame(columns=["Name","Category","Description","Location","Date","Image"]).to_csv("lost_reports.csv", index=False)

if not os.path.exists("found_reports.csv"):
    pd.DataFrame(columns=["Name","Category","Description","Location","Date","Image"]).to_csv("found_reports.csv", index=False)

def image_similarity(img1_path, img2_path):
    try:
        img1 = cv2.imread(img1_path)
        img2 = cv2.imread(img2_path)

        img1 = cv2.resize(img1, (300, 300))
        img2 = cv2.resize(img2, (300, 300))

        hist1 = cv2.calcHist([img1],[0],None,[256],[0,256])
        hist2 = cv2.calcHist([img2],[0],None,[256],[0,256])

        cv2.normalize(hist1, hist1)
        cv2.normalize(hist2, hist2)

        score = cv2.compareHist(hist1, hist2, cv2.HISTCMP_CORREL)
        score = max(0, min(100, score * 100))
        return round(score, 2)
    except:
        return 0

def text_similarity(a, b):
    return round(SequenceMatcher(None, str(a), str(b)).ratio() * 100, 2)

st.title("🔍 FindBack")
st.caption("Smart Missing & Found Matching System")

menu = st.sidebar.selectbox(
    "Menu",
    ["Add Lost Report", "Add Found Report", "Find Matches"]
)

if menu == "Add Lost Report":
    st.header("Add Lost Report")

    name = st.text_input("Name")
    category = st.selectbox("Category", ["Object","Person","Pet"])
    desc = st.text_area("Description")
    loc = st.text_input("Location")
    date = st.date_input("Date")
    image = st.file_uploader("Image", type=["jpg","jpeg","png"])

    if st.button("Save Lost Report"):
        img_path = ""
        if image:
            img_path = os.path.join("uploads/lost", image.name)
            with open(img_path, "wb") as f:
                f.write(image.getbuffer())

        row = pd.DataFrame([[name,category,desc,loc,str(date),img_path]],
                           columns=["Name","Category","Description","Location","Date","Image"])

        df = pd.read_csv("lost_reports.csv")
        df = pd.concat([df,row], ignore_index=True)
        df.to_csv("lost_reports.csv", index=False)

        st.success("Saved successfully!")

elif menu == "Add Found Report":
    st.header("Add Found Report")

    name = st.text_input("Name")
    category = st.selectbox("Category", ["Object","Person","Pet"])
    desc = st.text_area("Description")
    loc = st.text_input("Location")
    date = st.date_input("Date")
    image = st.file_uploader("Image", type=["jpg","jpeg","png"])

    if st.button("Save Found Report"):
        img_path = ""
        if image:
            img_path = os.path.join("uploads/found", image.name)
            with open(img_path, "wb") as f:
                f.write(image.getbuffer())

        row = pd.DataFrame([[name,category,desc,loc,str(date),img_path]],
                           columns=["Name","Category","Description","Location","Date","Image"])

        df = pd.read_csv("found_reports.csv")
        df = pd.concat([df,row], ignore_index=True)
        df.to_csv("found_reports.csv", index=False)

        st.success("Saved successfully!")

else:
    st.header("Match Results")

    lost_df = pd.read_csv("lost_reports.csv")
    found_df = pd.read_csv("found_reports.csv")

    results = []

    for _, lost in lost_df.iterrows():
        for _, found in found_df.iterrows():

            if lost["Category"] != found["Category"]:
                continue

            desc_score = text_similarity(
                lost["Description"],
                found["Description"]
            )

            location_score = 100 if str(lost["Location"]).lower() == str(found["Location"]).lower() else 40

            img_score = 0
            if str(lost["Image"]) and str(found["Image"]):
                if os.path.exists(str(lost["Image"])) and os.path.exists(str(found["Image"])):
                    img_score = image_similarity(
                        str(lost["Image"]),
                        str(found["Image"])
                    )

            final_score = (
                0.50 * desc_score +
                0.20 * location_score +
                0.30 * img_score
            )

            results.append({
                "Lost": lost["Name"],
                "Found": found["Name"],
                "Description Score": round(desc_score,2),
                "Location Score": round(location_score,2),
                "Image Score": round(img_score,2),
                "Final Match %": round(final_score,2)
            })

    if results:
        result_df = pd.DataFrame(results)
        result_df = result_df.sort_values(
            by="Final Match %",
            ascending=False
        )

        st.dataframe(result_df, use_container_width=True)

        top = result_df.iloc[0]["Final Match %"]
        if top >= 80:
            st.success(f"Possible strong match found! ({top}%)")
    else:
        st.warning("No data available.")
