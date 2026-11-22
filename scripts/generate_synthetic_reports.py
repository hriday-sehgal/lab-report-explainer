#!/usr/bin/env python3
"""
Synthetic Lab Report & Ground Truth Generator
Generates 15 synthetic medical laboratory reports in PDF format along with
their corresponding ground truth JSON files across 5 diagnostic panels:
1. CBC (Complete Blood Count)
2. Lipid Profile
3. HbA1c (Glycated Hemoglobin)
4. Thyroid Profile (TSH, Total T3, Total T4)
5. Liver Function Test (LFT)
"""

import os
import json
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

OUTPUT_PDF_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../data/synthetic_reports"))
OUTPUT_GT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../data/ground_truth"))

REPORTS_DATA = [
    {
        "report_id": "LAB-001",
        "panel_name": "COMPLETE BLOOD COUNT (CBC)",
        "report_type": "CBC",
        "patient": {"name": "Aarav Sharma", "age": 28, "gender": "Male", "id": "PT-1001", "ref_dr": "Self / Wellness"},
        "date": "2026-11-15",
        "notes": "Routine health checkup. Patient asymptomatic.",
        "tests": [
            {"test_name": "Hemoglobin", "value": 14.8, "unit": "g/dL", "ref_low": 13.0, "ref_high": 17.0, "expected_flag": "normal", "is_critical": False},
            {"test_name": "RBC Count", "value": 4.9, "unit": "mil/uL", "ref_low": 4.5, "ref_high": 5.9, "expected_flag": "normal", "is_critical": False},
            {"test_name": "Packed Cell Volume (PCV)", "value": 44.0, "unit": "%", "ref_low": 40.0, "ref_high": 50.0, "expected_flag": "normal", "is_critical": False},
            {"test_name": "Total Leukocyte Count (WBC)", "value": 6800, "unit": "/uL", "ref_low": 4000, "ref_high": 11000, "expected_flag": "normal", "is_critical": False},
            {"test_name": "Platelet Count", "value": 240000, "unit": "/uL", "ref_low": 150000, "ref_high": 450000, "expected_flag": "normal", "is_critical": False},
        ],
        "expected_next_step": "no_action"
    },
    {
        "report_id": "LAB-002",
        "panel_name": "COMPLETE BLOOD COUNT (CBC)",
        "report_type": "CBC",
        "patient": {"name": "Priya Nair", "age": 31, "gender": "Female", "id": "PT-1002", "ref_dr": "Dr. S. K. Gupta"},
        "date": "2026-11-16",
        "notes": "Patient complains of generalized fatigue and lethargy.",
        "tests": [
            {"test_name": "Hemoglobin", "value": 9.4, "unit": "g/dL", "ref_low": 12.0, "ref_high": 15.0, "expected_flag": "low", "is_critical": False},
            {"test_name": "RBC Count", "value": 3.7, "unit": "mil/uL", "ref_low": 3.8, "ref_high": 4.8, "expected_flag": "low", "is_critical": False},
            {"test_name": "Packed Cell Volume (PCV)", "value": 31.0, "unit": "%", "ref_low": 36.0, "ref_high": 46.0, "expected_flag": "low", "is_critical": False},
            {"test_name": "Total Leukocyte Count (WBC)", "value": 7200, "unit": "/uL", "ref_low": 4000, "ref_high": 11000, "expected_flag": "normal", "is_critical": False},
            {"test_name": "Platelet Count", "value": 210000, "unit": "/uL", "ref_low": 150000, "ref_high": 450000, "expected_flag": "normal", "is_critical": False},
        ],
        "expected_next_step": "doctor_consult"
    },
    {
        "report_id": "LAB-003",
        "panel_name": "COMPLETE BLOOD COUNT (CBC) - CRITICAL VALUE",
        "report_type": "CBC",
        "patient": {"name": "Rohan Deshmukh", "age": 42, "gender": "Male", "id": "PT-1003", "ref_dr": "Emergency Clinic"},
        "date": "2026-11-17",
        "notes": "CRITICAL PANIC VALUE ALERT: Severe thrombocytopenia detected.",
        "tests": [
            {"test_name": "Hemoglobin", "value": 13.2, "unit": "g/dL", "ref_low": 13.0, "ref_high": 17.0, "expected_flag": "normal", "is_critical": False},
            {"test_name": "Total Leukocyte Count (WBC)", "value": 5400, "unit": "/uL", "ref_low": 4000, "ref_high": 11000, "expected_flag": "normal", "is_critical": False},
            {"test_name": "Platelet Count", "value": 14000, "unit": "/uL", "ref_low": 150000, "ref_high": 450000, "expected_flag": "critical_low", "is_critical": True},
        ],
        "expected_next_step": "doctor_consult"
    },
    {
        "report_id": "LAB-004",
        "panel_name": "LIPID PROFILE - FASTING",
        "report_type": "LIPID",
        "patient": {"name": "Sunita Verma", "age": 45, "gender": "Female", "id": "PT-1004", "ref_dr": "Dr. R. K. Saxena"},
        "date": "2026-11-17",
        "notes": "12 hours overnight fasting. Routine annual lipid assessment.",
        "tests": [
            {"test_name": "Total Cholesterol", "value": 175.0, "unit": "mg/dL", "ref_low": 125.0, "ref_high": 200.0, "expected_flag": "normal", "is_critical": False},
            {"test_name": "HDL Cholesterol", "value": 52.0, "unit": "mg/dL", "ref_low": 40.0, "ref_high": 60.0, "expected_flag": "normal", "is_critical": False},
            {"test_name": "LDL Cholesterol", "value": 96.0, "unit": "mg/dL", "ref_low": 50.0, "ref_high": 100.0, "expected_flag": "normal", "is_critical": False},
            {"test_name": "Triglycerides", "value": 135.0, "unit": "mg/dL", "ref_low": 50.0, "ref_high": 150.0, "expected_flag": "normal", "is_critical": False},
            {"test_name": "VLDL Cholesterol", "value": 27.0, "unit": "mg/dL", "ref_low": 5.0, "ref_high": 30.0, "expected_flag": "normal", "is_critical": False},
        ],
        "expected_next_step": "no_action"
    },
    {
        "report_id": "LAB-005",
        "panel_name": "LIPID PROFILE - FASTING",
        "report_type": "LIPID",
        "patient": {"name": "Vikram Malhotra", "age": 52, "gender": "Male", "id": "PT-1005", "ref_dr": "Dr. A. B. Joshi"},
        "date": "2026-11-18",
        "notes": "Elevated atherogenic lipoprotein markers.",
        "tests": [
            {"test_name": "Total Cholesterol", "value": 248.0, "unit": "mg/dL", "ref_low": 125.0, "ref_high": 200.0, "expected_flag": "high", "is_critical": False},
            {"test_name": "HDL Cholesterol", "value": 36.0, "unit": "mg/dL", "ref_low": 40.0, "ref_high": 60.0, "expected_flag": "low", "is_critical": False},
            {"test_name": "LDL Cholesterol", "value": 164.0, "unit": "mg/dL", "ref_low": 50.0, "ref_high": 100.0, "expected_flag": "high", "is_critical": False},
            {"test_name": "Triglycerides", "value": 240.0, "unit": "mg/dL", "ref_low": 50.0, "ref_high": 150.0, "expected_flag": "high", "is_critical": False},
        ],
        "expected_next_step": "doctor_consult"
    },
    {
        "report_id": "LAB-006",
        "panel_name": "LIPID PROFILE - FASTING (HYPERTRIGLYCERIDEMIA)",
        "report_type": "LIPID",
        "patient": {"name": "Meera Iyer", "age": 39, "gender": "Female", "id": "PT-1006", "ref_dr": "Dr. P. Sethi"},
        "date": "2026-11-18",
        "notes": "Isolated high triglycerides.",
        "tests": [
            {"test_name": "Total Cholesterol", "value": 195.0, "unit": "mg/dL", "ref_low": 125.0, "ref_high": 200.0, "expected_flag": "normal", "is_critical": False},
            {"test_name": "HDL Cholesterol", "value": 46.0, "unit": "mg/dL", "ref_low": 40.0, "ref_high": 60.0, "expected_flag": "normal", "is_critical": False},
            {"test_name": "LDL Cholesterol", "value": 98.0, "unit": "mg/dL", "ref_low": 50.0, "ref_high": 100.0, "expected_flag": "normal", "is_critical": False},
            {"test_name": "Triglycerides", "value": 290.0, "unit": "mg/dL", "ref_low": 50.0, "ref_high": 150.0, "expected_flag": "high", "is_critical": False},
        ],
        "expected_next_step": "follow_up_test_package"
    },
    {
        "report_id": "LAB-007",
        "panel_name": "DIABETES MONITORING (HbA1c & GLUCOSE)",
        "report_type": "HBA1C",
        "patient": {"name": "Ananya Sen", "age": 26, "gender": "Female", "id": "PT-1007", "ref_dr": "Dr. M. Roy"},
        "date": "2026-11-19",
        "notes": "Non-diabetic reference parameters confirmed.",
        "tests": [
            {"test_name": "HbA1c (Glycated Hemoglobin)", "value": 5.2, "unit": "%", "ref_low": 4.0, "ref_high": 5.6, "expected_flag": "normal", "is_critical": False},
            {"test_name": "Estimated Average Glucose (eAG)", "value": 103.0, "unit": "mg/dL", "ref_low": 70.0, "ref_high": 115.0, "expected_flag": "normal", "is_critical": False},
        ],
        "expected_next_step": "no_action"
    },
    {
        "report_id": "LAB-008",
        "panel_name": "DIABETES MONITORING (HbA1c)",
        "report_type": "HBA1C",
        "patient": {"name": "Rajesh Khanna", "age": 58, "gender": "Male", "id": "PT-1008", "ref_dr": "Dr. K. Patel"},
        "date": "2026-11-19",
        "notes": "Suboptimal glycemic status.",
        "tests": [
            {"test_name": "HbA1c (Glycated Hemoglobin)", "value": 8.7, "unit": "%", "ref_low": 4.0, "ref_high": 5.6, "expected_flag": "high", "is_critical": False},
            {"test_name": "Estimated Average Glucose (eAG)", "value": 203.0, "unit": "mg/dL", "ref_low": 70.0, "ref_high": 115.0, "expected_flag": "high", "is_critical": False},
        ],
        "expected_next_step": "doctor_consult"
    },
    {
        "report_id": "LAB-009",
        "panel_name": "THYROID PROFILE - TOTAL",
        "report_type": "THYROID",
        "patient": {"name": "Kavita Rao", "age": 34, "gender": "Female", "id": "PT-1009", "ref_dr": "Dr. S. Venkat"},
        "date": "2026-11-19",
        "notes": "Evaluation for unexplained weight gain and cold intolerance.",
        "tests": [
            {"test_name": "Thyroid Stimulating Hormone (TSH)", "value": 7.85, "unit": "uIU/mL", "ref_low": 0.45, "ref_high": 4.50, "expected_flag": "high", "is_critical": False},
            {"test_name": "Total Triiodothyronine (T3)", "value": 1.10, "unit": "ng/mL", "ref_low": 0.80, "ref_high": 2.00, "expected_flag": "normal", "is_critical": False},
            {"test_name": "Total Thyroxine (T4)", "value": 6.4, "unit": "ug/dL", "ref_low": 5.1, "ref_high": 14.1, "expected_flag": "normal", "is_critical": False},
        ],
        "expected_next_step": "doctor_consult"
    },
    {
        "report_id": "LAB-010",
        "panel_name": "THYROID PROFILE - TOTAL",
        "report_type": "THYROID",
        "patient": {"name": "Deepak Bhatia", "age": 41, "gender": "Male", "id": "PT-1010", "ref_dr": "Dr. G. Oberoi"},
        "date": "2026-11-20",
        "notes": "Low TSH finding with clinical palpitations.",
        "tests": [
            {"test_name": "Thyroid Stimulating Hormone (TSH)", "value": 0.08, "unit": "uIU/mL", "ref_low": 0.45, "ref_high": 4.50, "expected_flag": "low", "is_critical": False},
            {"test_name": "Total Triiodothyronine (T3)", "value": 2.45, "unit": "ng/mL", "ref_low": 0.80, "ref_high": 2.00, "expected_flag": "high", "is_critical": False},
            {"test_name": "Total Thyroxine (T4)", "value": 15.8, "unit": "ug/dL", "ref_low": 5.1, "ref_high": 14.1, "expected_flag": "high", "is_critical": False},
        ],
        "expected_next_step": "doctor_consult"
    },
    {
        "report_id": "LAB-011",
        "panel_name": "LIVER FUNCTION TEST (LFT)",
        "report_type": "LFT",
        "patient": {"name": "Gaurav Kapoor", "age": 36, "gender": "Male", "id": "PT-1011", "ref_dr": "Dr. T. Choudhury"},
        "date": "2026-11-20",
        "notes": "Evaluation for transaminitis.",
        "tests": [
            {"test_name": "Alanine Aminotransferase (ALT/SGPT)", "value": 112.0, "unit": "U/L", "ref_low": 10.0, "ref_high": 50.0, "expected_flag": "high", "is_critical": False},
            {"test_name": "Aspartate Aminotransferase (AST/SGOT)", "value": 88.0, "unit": "U/L", "ref_low": 10.0, "ref_high": 45.0, "expected_flag": "high", "is_critical": False},
            {"test_name": "Alkaline Phosphatase (ALP)", "value": 95.0, "unit": "U/L", "ref_low": 40.0, "ref_high": 130.0, "expected_flag": "normal", "is_critical": False},
            {"test_name": "Total Bilirubin", "value": 0.9, "unit": "mg/dL", "ref_low": 0.2, "ref_high": 1.2, "expected_flag": "normal", "is_critical": False},
            {"test_name": "Serum Albumin", "value": 4.2, "unit": "g/dL", "ref_low": 3.5, "ref_high": 5.2, "expected_flag": "normal", "is_critical": False},
        ],
        "expected_next_step": "doctor_consult"
    },
    {
        "report_id": "LAB-012",
        "panel_name": "LIVER FUNCTION TEST (LFT) - CRITICAL VALUE",
        "report_type": "LFT",
        "patient": {"name": "Lakshmi Narayanan", "age": 62, "gender": "Female", "id": "PT-1012", "ref_dr": "Gastroenterology Ward"},
        "date": "2026-11-20",
        "notes": "CRITICAL PANIC VALUE ALERT: Deep icterus, high total bilirubin.",
        "tests": [
            {"test_name": "Total Bilirubin", "value": 16.5, "unit": "mg/dL", "ref_low": 0.2, "ref_high": 1.2, "expected_flag": "critical_high", "is_critical": True},
            {"test_name": "Direct Bilirubin", "value": 11.2, "unit": "mg/dL", "ref_low": 0.0, "ref_high": 0.3, "expected_flag": "high", "is_critical": False},
            {"test_name": "Alanine Aminotransferase (ALT/SGPT)", "value": 240.0, "unit": "U/L", "ref_low": 10.0, "ref_high": 50.0, "expected_flag": "high", "is_critical": False},
            {"test_name": "Alkaline Phosphatase (ALP)", "value": 310.0, "unit": "U/L", "ref_low": 40.0, "ref_high": 130.0, "expected_flag": "high", "is_critical": False},
        ],
        "expected_next_step": "doctor_consult"
    },
    {
        "report_id": "LAB-013",
        "panel_name": "METABOLIC HEALTH PANEL (HbA1c & LIPID)",
        "report_type": "MULTI",
        "patient": {"name": "Siddharth Jain", "age": 49, "gender": "Male", "id": "PT-1013", "ref_dr": "Dr. N. K. Bansal"},
        "date": "2026-11-21",
        "notes": "Combined metabolic screening.",
        "tests": [
            {"test_name": "HbA1c (Glycated Hemoglobin)", "value": 6.8, "unit": "%", "ref_low": 4.0, "ref_high": 5.6, "expected_flag": "high", "is_critical": False},
            {"test_name": "Total Cholesterol", "value": 218.0, "unit": "mg/dL", "ref_low": 125.0, "ref_high": 200.0, "expected_flag": "high", "is_critical": False},
            {"test_name": "Triglycerides", "value": 210.0, "unit": "mg/dL", "ref_low": 50.0, "ref_high": 150.0, "expected_flag": "high", "is_critical": False},
            {"test_name": "HDL Cholesterol", "value": 38.0, "unit": "mg/dL", "ref_low": 40.0, "ref_high": 60.0, "expected_flag": "low", "is_critical": False},
        ],
        "expected_next_step": "doctor_consult"
    },
    {
        "report_id": "LAB-014",
        "panel_name": "COMPLETE BLOOD COUNT (CBC) - LEUKOCYTOSIS",
        "report_type": "CBC",
        "patient": {"name": "Harish Pandey", "age": 38, "gender": "Male", "id": "PT-1014", "ref_dr": "Dr. V. Singhal"},
        "date": "2026-11-21",
        "notes": "Patient presenting with acute pharyngitis and high fever.",
        "tests": [
            {"test_name": "Hemoglobin", "value": 14.1, "unit": "g/dL", "ref_low": 13.0, "ref_high": 17.0, "expected_flag": "normal", "is_critical": False},
            {"test_name": "Total Leukocyte Count (WBC)", "value": 18500, "unit": "/uL", "ref_low": 4000, "ref_high": 11000, "expected_flag": "high", "is_critical": False},
            {"test_name": "Neutrophils", "value": 84, "unit": "%", "ref_low": 40, "ref_high": 75, "expected_flag": "high", "is_critical": False},
            {"test_name": "Lymphocytes", "value": 12, "unit": "%", "ref_low": 20, "ref_high": 45, "expected_flag": "low", "is_critical": False},
            {"test_name": "Platelet Count", "value": 310000, "unit": "/uL", "ref_low": 150000, "ref_high": 450000, "expected_flag": "normal", "is_critical": False},
        ],
        "expected_next_step": "doctor_consult"
    },
    {
        "report_id": "LAB-015",
        "panel_name": "COMPLETE BLOOD COUNT (CBC) - CRITICAL VALUE",
        "report_type": "CBC",
        "patient": {"name": "Fatima Begum", "age": 67, "gender": "Female", "id": "PT-1015", "ref_dr": "Emergency Medical Dept"},
        "date": "2026-11-21",
        "notes": "CRITICAL PANIC VALUE ALERT: Severe life-threatening anemia.",
        "tests": [
            {"test_name": "Hemoglobin", "value": 5.6, "unit": "g/dL", "ref_low": 12.0, "ref_high": 15.0, "expected_flag": "critical_low", "is_critical": True},
            {"test_name": "RBC Count", "value": 1.9, "unit": "mil/uL", "ref_low": 3.8, "ref_high": 4.8, "expected_flag": "low", "is_critical": False},
            {"test_name": "Packed Cell Volume (PCV)", "value": 17.5, "unit": "%", "ref_low": 36.0, "ref_high": 46.0, "expected_flag": "low", "is_critical": False},
            {"test_name": "Total Leukocyte Count (WBC)", "value": 5200, "unit": "/uL", "ref_low": 4000, "ref_high": 11000, "expected_flag": "normal", "is_critical": False},
            {"test_name": "Platelet Count", "value": 185000, "unit": "/uL", "ref_low": 150000, "ref_high": 450000, "expected_flag": "normal", "is_critical": False},
        ],
        "expected_next_step": "doctor_consult"
    }
]

def build_pdf(report, output_path):
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )
    
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'LabTitle',
        parent=styles['Normal'],
        fontSize=15,
        leading=18,
        textColor=colors.HexColor('#0F294A'),
        fontName='Helvetica-Bold'
    )
    subtitle_style = ParagraphStyle(
        'LabSubTitle',
        parent=styles['Normal'],
        fontSize=8,
        leading=10,
        textColor=colors.HexColor('#555555')
    )
    panel_title_style = ParagraphStyle(
        'PanelTitle',
        parent=styles['Normal'],
        fontSize=11,
        leading=14,
        textColor=colors.HexColor('#0F294A'),
        fontName='Helvetica-Bold'
    )
    body_style = ParagraphStyle(
        'LabBody',
        parent=styles['Normal'],
        fontSize=8,
        leading=11
    )
    alert_style = ParagraphStyle(
        'AlertBody',
        parent=styles['Normal'],
        fontSize=8,
        leading=11,
        textColor=colors.HexColor('#C53030'),
        fontName='Helvetica-Bold'
    )
    
    story = []
    
    # Header Table: Lab Branding
    header_data = [
        [
            Paragraph("<b>METRO-CARE DIAGNOSTICS & PATHOLOGY LABS</b><br/><font size=7 color='#666'>Accredited Quality Laboratory | NABL Certified Equivalent | ISO 15189:2022</font>", title_style),
            Paragraph("<b>Report ID:</b> " + report["report_id"] + "<br/><b>Sample Date:</b> " + report["date"] + "<br/><b>Status:</b> Final Validated", subtitle_style)
        ]
    ]
    header_table = Table(header_data, colWidths=[360, 180])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(header_table)
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#0F294A'), spaceBefore=4, spaceAfter=8))
    
    # Patient Demographic Block
    patient = report["patient"]
    patient_data = [
        [
            Paragraph(f"<b>Patient Name:</b> {patient['name']}", body_style),
            Paragraph(f"<b>Age / Sex:</b> {patient['age']} Yrs / {patient['gender']}", body_style),
            Paragraph(f"<b>Patient ID:</b> {patient['id']}", body_style)
        ],
        [
            Paragraph(f"<b>Referred By:</b> {patient['ref_dr']}", body_style),
            Paragraph(f"<b>Specimen:</b> Whole Blood / Serum", body_style),
            Paragraph(f"<b>Report Released:</b> {report['date']}", body_style)
        ]
    ]
    patient_table = Table(patient_data, colWidths=[200, 180, 160])
    patient_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F8FAFC')),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(patient_table)
    story.append(Spacer(1, 10))
    
    # Department / Investigation Banner
    story.append(Paragraph(f"DEPARTMENT OF HEMATOLOGY & CLINICAL BIOCHEMISTRY — {report['panel_name']}", panel_title_style))
    story.append(Spacer(1, 4))
    
    # Test Results Table
    table_rows = [
        [
            Paragraph("<b>Investigation (Test Name)</b>", body_style),
            Paragraph("<b>Result Value</b>", body_style),
            Paragraph("<b>Unit</b>", body_style),
            Paragraph("<b>Biological Reference Interval</b>", body_style),
            Paragraph("<b>Status Flag</b>", body_style)
        ]
    ]
    
    for item in report["tests"]:
        val_str = f"{item['value']:g}" if isinstance(item['value'], (int, float)) else str(item['value'])
        ref_str = f"{item['ref_low']} - {item['ref_high']}"
        
        # Color coding flags
        flag = item["expected_flag"].upper()
        if "CRITICAL" in flag:
            flag_text = f"<font color='#B91C1C'><b>*** {flag} ***</b></font>"
            val_text = f"<font color='#B91C1C'><b>{val_str}</b></font>"
        elif flag == "HIGH":
            flag_text = "<font color='#D97706'><b>HIGH</b></font>"
            val_text = f"<b>{val_str}</b>"
        elif flag == "LOW":
            flag_text = "<font color='#2563EB'><b>LOW</b></font>"
            val_text = f"<b>{val_str}</b>"
        else:
            flag_text = "<font color='#16A34A'>NORMAL</font>"
            val_text = val_str
            
        table_rows.append([
            Paragraph(item["test_name"], body_style),
            Paragraph(val_text, body_style),
            Paragraph(item["unit"], body_style),
            Paragraph(ref_str, body_style),
            Paragraph(flag_text, body_style)
        ])
    
    result_table = Table(table_rows, colWidths=[200, 75, 75, 115, 75])
    result_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#0F294A')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('BOTTOMPADDING', (0,0), (-1,0), 5),
        ('TOPPADDING', (0,0), (-1,0), 5),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#F8FAFC')]),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,1), (-1,-1), 4),
        ('BOTTOMPADDING', (0,1), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 5),
        ('RIGHTPADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(result_table)
    story.append(Spacer(1, 10))
    
    # Clinical Notes Block
    notes_color = '#FEF2F2' if any(t.get('is_critical') for t in report['tests']) else '#F1F5F9'
    border_color = '#EF4444' if any(t.get('is_critical') for t in report['tests']) else '#94A3B8'
    
    notes_p = Paragraph(f"<b>Pathologist Remarks:</b> {report['notes']}", alert_style if any(t.get('is_critical') for t in report['tests']) else body_style)
    notes_table = Table([[notes_p]], colWidths=[540])
    notes_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor(notes_color)),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor(border_color)),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(notes_table)
    story.append(Spacer(1, 15))
    
    # Sign-off & Disclaimer Footer
    footer_data = [
        [
            Paragraph("<font size=6.5 color='#64748B'><b>END OF EXAMINATION REPORT</b><br/>This is an authenticated computer generated report validated by automated clinical analyzers. Results relate specifically to the specimen submitted. Clinical correlation advised.</font>", body_style),
            Paragraph("<b>Dr. Arvind K. Sharma, MD</b><br/><font size=7 color='#475569'>Consultant Pathologist & Lab Director<br/>Reg. No: MCI-2009-48211</font>", body_style)
        ]
    ]
    footer_table = Table(footer_data, colWidths=[380, 160])
    footer_table.setStyle(TableStyle([
        ('LINEABOVE', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
    ]))
    story.append(footer_table)
    
    doc.build(story)

def main():
    os.makedirs(OUTPUT_PDF_DIR, exist_ok=True)
    os.makedirs(OUTPUT_GT_DIR, exist_ok=True)
    
    print(f"Generating 15 synthetic lab reports in: {OUTPUT_PDF_DIR}")
    for rep in REPORTS_DATA:
        rep_id = rep["report_id"]
        pdf_path = os.path.join(OUTPUT_PDF_DIR, f"{rep_id}.pdf")
        gt_path = os.path.join(OUTPUT_GT_DIR, f"{rep_id}.json")
        
        # Build PDF
        build_pdf(rep, pdf_path)
        
        # Write Ground Truth JSON
        with open(gt_path, "w", encoding="utf-8") as f:
            json.dump(rep, f, indent=2)
            
        print(f"  [✓] Generated {rep_id}.pdf and {rep_id}.json ({rep['report_type']} - {rep['panel_name']})")

    print("\nAll 15 synthetic reports and ground truth datasets successfully generated.")

if __name__ == "__main__":
    main()
