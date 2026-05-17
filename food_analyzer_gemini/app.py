import json
import os
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv
from PIL import Image

from utils.gemini_utils import analyze_food_image, DEFAULT_MODEL

load_dotenv()

APP_TITLE = "Food Image Analyzer"
APP_ICON = "🍔"

st.set_page_config(
    page_title=APP_TITLE,
    page_icon=APP_ICON,
    layout="wide",
    initial_sidebar_state="expanded",
)

# Load CSS
css_path = Path("assets/style.css")
if css_path.exists():
    st.markdown(f"<style>{css_path.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)


def safe_get(d, key, default):
    return d[key] if isinstance(d, dict) and key in d else default


def render_tag_list(items):
    if not items:
        st.write("Not found")
        return
    for item in items:
        st.markdown(f'<span class="badge">{item}</span>', unsafe_allow_html=True)


def main():
    st.markdown(
        """
        <div class="hero">
            <h1>Food Image Analyzer</h1>
            <p>Upload or capture a food item image, then Gemini will estimate ingredients, age suitability, nutrition, allergens, and health notes.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.sidebar:
        st.markdown("## Settings")
        api_key = st.text_input(
            "Gemini API Key",
            value=os.getenv("GEMINI_API_KEY", ""),
            type="password",
            help="Your Google Gemini API key",
        )

        model = st.selectbox(
            "Model",
            options=[
                "gemini-3.1-flash-lite",
                "gemini-3.1-pro-preview",
            ],
            index=0,
            help="Flash-Lite is faster and cheaper; Pro is better for deeper reasoning.",
        )

        st.markdown("---")
        st.markdown("### About")
        st.caption(
            "This app gives an estimated analysis from the image. "
            "Age suitability and health notes are general guidance only."
        )

    tab_upload, tab_camera = st.tabs(["📤 Upload Image", "📷 Camera"])

    uploaded_image = None

    with tab_upload:
        uploaded_file = st.file_uploader(
            "Choose a food image",
            type=["png", "jpg", "jpeg", "webp"],
            accept_multiple_files=False,
        )
        if uploaded_file:
            uploaded_image = Image.open(uploaded_file).convert("RGB")
            st.image(uploaded_image, caption="Uploaded Image", use_container_width=True)

    with tab_camera:
        camera_file = st.camera_input("Take a live photo")
        if camera_file:
            uploaded_image = Image.open(camera_file).convert("RGB")
            st.image(uploaded_image, caption="Captured Image", use_container_width=True)

    col1, col2 = st.columns([1, 1])

    with col1:
        analyze_btn = st.button("Analyze Food Image", use_container_width=True)

    with col2:
        st.info("Best results come from a clear, well-lit image with the label visible.")

    if analyze_btn:
        if not api_key:
            st.error("Please enter your Gemini API key in the sidebar.")
            return

        if uploaded_image is None:
            st.error("Please upload or capture an image first.")
            return

        with st.spinner("Analyzing image with Gemini..."):
            try:
                result = analyze_food_image(
                    image=uploaded_image,
                    api_key=api_key,
                    model=model,
                )
                st.session_state["analysis_result"] = result
            except Exception as e:
                st.error(f"Analysis failed: {e}")
                return

    result = st.session_state.get("analysis_result")

    if result:
        st.markdown("## Analysis Result")

        item_name = safe_get(result, "item_name", "Unknown")
        category = safe_get(result, "category", "Unknown")
        confidence = safe_get(result, "confidence", "low")
        suitable_age = safe_get(result, "suitable_age_group", {})
        nutrition = safe_get(result, "nutrition_summary", {})
        detected = safe_get(result, "ingredients_detected", [])
        likely = safe_get(result, "ingredients_likely", [])
        allergens = safe_get(result, "allergen_risks", [])
        notes = safe_get(result, "health_notes", [])
        conclusion = safe_get(result, "short_conclusion", "")

        k1, k2, k3 = st.columns(3)
        k1.metric("Item", item_name)
        k2.metric("Category", category)
        k3.metric("Confidence", confidence.title())

        st.markdown('<div class="card">', unsafe_allow_html=True)

        left, right = st.columns(2)

        with left:
            st.markdown('<div class="section-title">Ingredients Detected</div>', unsafe_allow_html=True)
            render_tag_list(detected)

            st.markdown('<div class="section-title" style="margin-top:16px;">Likely Ingredients</div>', unsafe_allow_html=True)
            render_tag_list(likely)

            st.markdown('<div class="section-title" style="margin-top:16px;">Allergen Risks</div>', unsafe_allow_html=True)
            render_tag_list(allergens)

        with right:
            st.markdown('<div class="section-title">Suitable Age Group</div>', unsafe_allow_html=True)
            st.markdown(
                f"""
                <div class="result-box">
                    <b>Group:</b> {safe_get(suitable_age, "group", "Unknown")}<br>
                    <b>Reason:</b> {safe_get(suitable_age, "reason", "Unknown")}
                </div>
                """,
                unsafe_allow_html=True,
            )

            st.markdown('<div class="section-title" style="margin-top:16px;">Nutrition Summary</div>', unsafe_allow_html=True)
            st.markdown(
                f"""
                <div class="result-box">
                    <b>Calories:</b> {safe_get(nutrition, "calories", "Unknown")}<br>
                    <b>Sugar:</b> {safe_get(nutrition, "sugar", "Unknown")}<br>
                    <b>Caffeine:</b> {safe_get(nutrition, "caffeine", "Unknown")}<br>
                    <b>Fat:</b> {safe_get(nutrition, "fat", "Unknown")}<br>
                    <b>Salt:</b> {safe_get(nutrition, "salt", "Unknown")}
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.markdown('<div class="section-title" style="margin-top:16px;">Health Notes</div>', unsafe_allow_html=True)
        if notes:
            for note in notes:
                st.write(f"• {note}")
        else:
            st.write("No health notes found.")

        if conclusion:
            st.markdown(f"**Conclusion:** {conclusion}")

        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("## Raw JSON")
        st.code(json.dumps(result, indent=2), language="json")

        st.download_button(
            label="Download JSON Result",
            data=json.dumps(result, indent=2),
            file_name="food_analysis.json",
            mime="application/json",
            use_container_width=True,
        )


if __name__ == "__main__":
    main()