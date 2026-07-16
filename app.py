import streamlit as st
import os
import re
from groq import Groq

# Page configuration
st.set_page_config(page_title="Solar PV & Battery Bank Sizer", page_icon="⚡", layout="centered")

# Streamlit secrets se key direct load karein
try:
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
except Exception:
    GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

client = Groq(api_key=GROQ_API_KEY)

def calculate_solar_system(daily_load_kwh, sun_hours, system_voltage, autonomy_days):
    try:
        load_wh = float(daily_load_kwh) * 1000
        v_sys = float(system_voltage)
        sun_h = float(sun_hours)
        days = float(autonomy_days)
        
        battery_ah = (load_wh * days) / (v_sys * 0.8 * 0.85)
        solar_kw = (load_wh * 1.3) / (sun_h * 1000)
        
        return {"solar_pv_kw": round(solar_kw, 2), "battery_bank_ah": round(battery_ah, 2), "status": "Success"}
    except Exception as e:
        return {"status": "Error", "message": str(e)}

# UI Design
st.title("⚡ AI-Powered Electrical Agent: Solar PV & Battery Bank Sizer")
st.write("Input your load parameters and system requirements below.")

# User input form
user_prompt = st.text_area(
    "User Prompt", 
    placeholder="e.g., Design a system for 15 kWh daily load with 5.5 sun hours on a 48V system.",
    height=100
)

if st.button("Submit", type="primary"):
    if not user_prompt.strip():
        st.warning("Please enter a system requirement first.")
    else:
        with st.spinner("Analyzing requirements and performing technical sizing calculations..."):
            system_instruction = (
                "You are an expert Electrical Power Systems Engineer specializing in Renewable Energy. "
                "Your task is to take the raw calculation data provided and present a highly professional, "
                "structured technical report for a Solar PV & Battery Storage installation. "
                "Use markdown headings and bullet points. Format the output professionally."
            )
            
            # Default values
            load, sun, voltage, days = 10.0, 5.5, 24, 1

            # Extracting parameters using regex
            load_match = re.search(r'(\d+(\.\d+)?)\s*(kwh|unit)', user_prompt.lower())
            if load_match: 
                load = float(load_match.group(1))
            
            sun_match = re.search(r'(\d+(\.\d+)?)\s*(hour|hr|sun)', user_prompt.lower())
            if sun_match: 
                sun = float(sun_match.group(1))

            volt_match = re.search(r'(\d+)\s*(v|volt)', user_prompt.lower())
            if volt_match: 
                v_val = int(volt_match.group(1))
                if v_val in [12, 24, 48]: 
                    voltage = v_val

            # Sizing Calculations
            calc_results = calculate_solar_system(load, sun, voltage, days)
            
            if calc_results["status"] == "Error":
                st.error("Error performing technical sizing calculations.")
            else:
                data_for_llm = (
                    f"User Request: '{user_prompt}'\n"
                    f"Calculated parameters: Load {load}kWh, Sun {sun}hr, Voltage {voltage}V, "
                    f"PV {calc_results['solar_pv_kw']}kW, Battery {calc_results['battery_bank_ah']}Ah. "
                    f"Generate report."
                )

                try:
                    # LLM API Call
                    completion = client.chat.completions.create(
                        model="llama-3.1-8b-instant",
                        messages=[
                            {"role": "system", "content": system_instruction}, 
                            {"role": "user", "content": data_for_llm}
                        ],
                        temperature=0.3
                    )
                    
                    # Displaying report
                    st.success("Technical Sizing Report Generated Successfully!")
                    st.markdown("---")
                    st.markdown(completion.choices[0].message.content)
                    
                except Exception as api_err:
                    st.error(f"API Error: {str(api_err)}")
