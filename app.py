import os
import gradio as gr
from groq import Groq

# Streamlit secrets se safe key load karein
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

def ee_solar_agent(user_prompt):
    system_instruction = (
        "You are an expert Electrical Power Systems Engineer specializing in Renewable Energy. "
        "Your task is to take the raw calculation data provided and present a highly professional, "
        "structured technical report for a Solar PV & Battery Storage installation. "
        "Use markdown headings and bullet points. Format the output professionally."
    )
    
    load, sun, voltage, days = 10, 5.5, 24, 1

    load_match = re.search(r'(\d+(\.\d+)?)\s*(kwh|unit)', user_prompt.lower())
    if load_match: load = float(load_match.group(1))
    
    sun_match = re.search(r'(\d+(\.\d+)?)\s*(hour|hr|sun)', user_prompt.lower())
    if sun_match: sun = float(sun_match.group(1))

    volt_match = re.search(r'(\d+)\s*(v|volt)', user_prompt.lower())
    if volt_match: 
        v_val = int(volt_match.group(1))
        if v_val in [12, 24, 48]: voltage = v_val

    calc_results = calculate_solar_system(load, sun, voltage, days)
    if calc_results["status"] == "Error": return "Error performing technical sizing calculations."

    data_for_llm = f"User Request: '{user_prompt}'\nCalculated parameters: Load {load}kWh, Sun {sun}hr, Voltage {voltage}V, PV {calc_results['solar_pv_kw']}kW, Battery {calc_results['battery_bank_ah']}Ah. Generate report."

    completion = client.chat.completions.create(
        model="llama3-8b-8192",
        messages=[{"role": "system", "content": system_instruction}, {"role": "user", "content": data_for_llm}],
        temperature=0.3
    )
    return completion.choices[0].message.content

interface = gr.Interface(
    fn=ee_solar_agent,
    inputs=gr.Textbox(lines=3, placeholder="e.g., Design a system for 15 kWh daily load with 5.5 sun hours on a 48V system.", label="user_prompt"),
    outputs=gr.Markdown(label="Solar PV & Battery Bank Sizing Report"),
    title="⚡ AI-Powered Electrical Agent: Solar PV & Battery Bank Sizer",
    description="Input your load parameters and system requirements."
)

if __name__ == "__main__":
    interface.launch()
