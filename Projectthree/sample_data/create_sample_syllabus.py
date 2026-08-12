import os
from pathlib import Path

def generate_sample_syllabus_pdf():
    pdf_path = Path(__file__).resolve().parent / "CS101_Syllabus.pdf"
    
    # Check if reportlab is installed, otherwise create text file or fallback PDF
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib import colors

        doc = SimpleDocTemplate(str(pdf_path), pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
        styles = getSampleStyleSheet()

        title_style = ParagraphStyle(
            'DocTitle',
            parent=styles['Heading1'],
            fontSize=22,
            leading=26,
            textColor=colors.HexColor("#1e293b"),
            spaceAfter=12
        )
        
        heading2 = ParagraphStyle(
            'DocHeading2',
            parent=styles['Heading2'],
            fontSize=14,
            leading=18,
            textColor=colors.HexColor("#2563eb"),
            spaceBefore=14,
            spaceAfter=6
        )

        body = ParagraphStyle(
            'DocBody',
            parent=styles['Normal'],
            fontSize=10,
            leading=14,
            textColor=colors.HexColor("#334155"),
            spaceAfter=6
        )

        elements = []

        # Course Header
        elements.append(Paragraph("CS 101: Introduction to Computer Science & Artificial Intelligence", title_style))
        elements.append(Paragraph("<b>Department of Computer Science — Fall Semester 2026</b>", body))
        elements.append(Spacer(1, 10))

        # Instructor Information
        elements.append(Paragraph("1. Course Information & Office Hours", heading2))
        info_data = [
            ["Instructor:", "Dr. Sarah Jenkins (sjenkins@university.edu)"],
            ["Office Hours:", "Tuesdays & Thursdays 2:00 PM – 4:00 PM (Tech Hall, Room 402)"],
            ["Head TA:", "Alex Rivera (arivera@university.edu)"],
            ["TA Office Hours:", "Wednesdays 10:00 AM – 12:00 PM & Fridays 1:00 PM – 3:00 PM"],
            ["Lecture Time:", "Monday / Wednesday 10:00 AM – 11:30 AM (Auditorium B)"]
        ]
        t = Table(info_data, colWidths=[120, 400])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#f8fafc")),
            ('TEXTCOLOR', (0,0), (-1,-1), colors.HexColor("#1e293b")),
            ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0,0), (-1,-1), 4),
            ('TOPPADDING', (0,0), (-1,-1), 4),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#e2e8f0")),
        ]))
        elements.append(t)
        elements.append(Spacer(1, 12))

        # Grading Policy
        elements.append(Paragraph("2. Grading Scheme & Policy", heading2))
        elements.append(Paragraph("Final grades are computed based on the following breakdown:", body))
        grade_data = [
            ["Component", "Weight", "Details"],
            ["Programming Assignments (4)", "30%", "Bi-weekly coding homework"],
            ["Midterm Examination", "25%", "In-class closed book exam"],
            ["Final Project & Presentation", "30%", "Group project building an AI app"],
            ["Quizzes & Participation", "15%", "Weekly pop quizzes on Canvas"]
        ]
        gt = Table(grade_data, colWidths=[180, 100, 240])
        gt.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#2563eb")),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0,0), (-1,-1), 5),
            ('TOPPADDING', (0,0), (-1,-1), 5),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
        ]))
        elements.append(gt)
        elements.append(Spacer(1, 12))

        # Late Submission Policy
        elements.append(Paragraph("3. Assignment Submissions & Late Policy", heading2))
        elements.append(Paragraph("• <b>Deadline Strictness:</b> All assignments are due by 11:59 PM EST on the designated due date via GitHub Classroom.", body))
        elements.append(Paragraph("• <b>Grace Days:</b> Each student receives <b>3 total slip days</b> for the entire semester. You may use at most 2 slip days per assignment without penalty.", body))
        elements.append(Paragraph("• <b>Late Penalty:</b> Once slip days are exhausted, late submissions incur a <b>15% penalty per 24-hour period</b>. Submissions over 48 hours late will receive 0 credit.", body))
        elements.append(Paragraph("• <b>Regrade Requests:</b> Regrade requests must be submitted within 7 days of receiving your grade via the Canvas portal.", body))
        elements.append(Spacer(1, 12))

        # Course Schedule & Key Deadlines
        elements.append(Paragraph("4. Schedule & Major Deadlines", heading2))
        sched_data = [
            ["Week / Date", "Topic", "Deliverables Due"],
            ["Week 2 (Sept 15)", "Python Basics & Data Structures", "Assignment 1 (Basics)"],
            ["Week 4 (Sept 29)", "Object-Oriented Programming", "Assignment 2 (OOP)"],
            ["Week 7 (Oct 20)", "Algorithms & Search", "Midterm Exam (Oct 22)"],
            ["Week 10 (Nov 10)", "Intro to ML & Vector Embeddings", "Assignment 3 (ML Intro)"],
            ["Week 12 (Nov 24)", "RAG & LLM Integration", "Assignment 4 (RAG App)"],
            ["Week 15 (Dec 15)", "Final Capstone Project Demos", "Final Project Code & Video"]
        ]
        st = Table(sched_data, colWidths=[130, 220, 170])
        st.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#0f172a")),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0,0), (-1,-1), 5),
            ('TOPPADDING', (0,0), (-1,-1), 5),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
        ]))
        elements.append(st)
        elements.append(Spacer(1, 12))

        # Academic Integrity & Materials
        elements.append(Paragraph("5. Textbooks & Academic Integrity", heading2))
        elements.append(Paragraph("<b>Required Textbook:</b> <i>Python Crash Course (3rd Edition)</i> by Eric Matthes. Supplementary readings will be posted on Canvas.", body))
        elements.append(Paragraph("<b>Academic Honesty:</b> Collaboration is encouraged on concepts, but all submitted code must be your own original work. Sharing direct solutions or plagiarizing online repositories will result in an F in the course and referral to the Honor Council.", body))

        doc.build(elements)
        print(f"Sample PDF successfully generated at {pdf_path}")

    except Exception as e:
        print(f"Reportlab build failed or not installed yet ({e}). Will run again after pip install.")

if __name__ == "__main__":
    generate_sample_syllabus_pdf()
