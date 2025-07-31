from flask import Flask, render_template, request, redirect, url_for
import pandas as pd
import os
import uuid
import json

app = Flask(__name__)

# File where supplier data is stored
DATA_FILE = 'TruSupply_Supplier_Risk_Analysis.xlsx'

# Load existing data or initialize new DataFrame
if os.path.exists(DATA_FILE):
    df = pd.read_excel(DATA_FILE)
else:
    df = pd.DataFrame(columns=[
        "Supplier ID", "Supplier Name", "Category", "Location",
        "Compliance Score", "Financial Score", "On-Time Delivery Rate", "Risk Score"
    ])

def save_data():
    df.to_excel(DATA_FILE, index=False)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    global df

    # Ensure numeric values
    numeric_cols = ["Compliance Score", "Financial Score", "On-Time Delivery Rate", "Risk Score"]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    df_clean = df.dropna(subset=numeric_cols)

    # Summary Stats
    total_suppliers = len(df_clean)
    avg_risk_score = round(df_clean["Risk Score"].mean(), 2)
    high_risk_count = len(df_clean[df_clean["Risk Score"] > 65])
    low_risk_count = len(df_clean[df_clean["Risk Score"] < 45])

    # Pie Chart: Category Distribution
    category_counts = df_clean['Category'].value_counts()
    category_chart_data = json.dumps({
        "labels": list(category_counts.index),
        "datasets": [{
            "label": "Category Distribution",
            "data": [int(x) for x in category_counts.values],
            "backgroundColor": [
                "#2563eb", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6", "#14b8a6"
            ]
        }]
    })

    # Bar Chart: Average Scores by Category
    grouped = df_clean.groupby("Category")[numeric_cols[:3]].mean().round(2)
    score_chart_data = json.dumps({
        "labels": grouped.index.tolist(),
        "datasets": [
            {"label": "Compliance", "data": grouped["Compliance Score"].tolist(), "backgroundColor": "#3b82f6"},
            {"label": "Financial", "data": grouped["Financial Score"].tolist(), "backgroundColor": "#10b981"},
            {"label": "Delivery", "data": grouped["On-Time Delivery Rate"].tolist(), "backgroundColor": "#f59e0b"}
        ]
    })

    # Line Chart: Risk Score Trends
    line_chart_data = json.dumps({
        "labels": df_clean['Supplier Name'].fillna(df_clean['Supplier ID']).tolist(),
        "datasets": [{
            "label": "Risk Score",
            "data": df_clean["Risk Score"].tolist(),
            "fill": False,
            "borderColor": "#ef4444",
            "tension": 0.1
        }]
    })

    return render_template('dashboard.html',
                           total_suppliers=total_suppliers,
                           avg_risk_score=avg_risk_score,
                           high_risk_count=high_risk_count,
                           low_risk_count=low_risk_count,
                           suppliers=df_clean.to_dict(orient='records'),
                           category_chart_data=category_chart_data,
                           score_chart_data=score_chart_data,
                           line_chart_data=line_chart_data)

@app.route('/evaluate')
def add_supplier():
    return render_template('form.html')

@app.route('/submit', methods=['POST'])
def submit():
    global df
    supplier_id = request.form['supplier_id'] or str(uuid.uuid4())[:8].upper()
    name = request.form['supplier_name'] or f"Supplier_{supplier_id}"
    category = request.form['category']
    location = request.form['location']
    compliance = float(request.form['compliance'])
    financial = float(request.form['financial'])
    delivery = float(request.form['delivery'])

    risk_score = round((compliance * 0.3 + financial * 0.4 + delivery * 0.3), 2)

    new_entry = {
        "Supplier ID": supplier_id,
        "Supplier Name": name,
        "Category": category,
        "Location": location,
        "Compliance Score": compliance,
        "Financial Score": financial,
        "On-Time Delivery Rate": delivery,
        "Risk Score": risk_score
    }

    df = pd.concat([df, pd.DataFrame([new_entry])], ignore_index=True)
    save_data()

    return render_template('result.html', risk_score=risk_score)

if __name__ == '__main__':
    app.run(debug=True)
