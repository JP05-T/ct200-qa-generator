from fpdf import FPDF


class ManualPDF(FPDF):
    def __init__(self):
        super().__init__()
        self.add_font("Arial", "", "C:\\Windows\\Fonts\\arial.ttf", uni=True)
        self.add_font("Arial", "B", "C:\\Windows\\Fonts\\arialbd.ttf", uni=True)
        self.add_font("Arial", "I", "C:\\Windows\\Fonts\\ariali.ttf", uni=True)
        self.add_font("Arial", "BI", "C:\\Windows\\Fonts\\arialbi.ttf", uni=True)

    def header(self):
        pass

    def footer(self):
        self.set_y(-15)
        self.set_font("Arial", "I", 8)
        self.cell(0, 10, f"Page {self.page_no()}/{{nb}}", align="C")

    def add_title(self, text):
        self.set_font("Arial", "B", 16)
        self.multi_cell(0, 10, text)
        self.ln(4)

    def add_h1(self, text):
        self.set_font("Arial", "B", 14)
        self.ln(4)
        self.multi_cell(0, 8, text)
        self.ln(2)

    def add_h2(self, text):
        self.set_font("Arial", "B", 12)
        self.ln(3)
        self.multi_cell(0, 7, text)
        self.ln(1)

    def add_h3(self, text):
        self.set_font("Arial", "B", 11)
        self.ln(2)
        self.multi_cell(0, 6, text)
        self.ln(1)

    def add_body(self, text):
        self.set_font("Arial", "", 10)
        self.multi_cell(0, 5, text)
        self.ln(2)

    def add_list_item(self, text):
        self.set_font("Arial", "", 10)
        self.set_x(self.l_margin + 5)
        self.multi_cell(0, 5, text)
        self.ln(1)

    def add_table(self, headers, rows):
        self.ln(3)
        num_cols = len(headers)
        col_width = (self.w - self.l_margin - self.r_margin) / num_cols

        self.set_font("Arial", "B", 9)
        self.set_fill_color(150, 150, 150)
        self.set_text_color(255, 255, 255)
        for h in headers:
            self.cell(col_width, 7, h, border=1, fill=True, align="C")
        self.ln()

        self.set_font("Arial", "", 9)
        self.set_text_color(0, 0, 0)
        for row in rows:
            max_h = 7
            for cell_val in row:
                lines = self.multi_cell(col_width, 5, cell_val, split_only=True)
                needed = len(lines) * 5
                if needed > max_h:
                    max_h = needed
            x_start = self.get_x()
            y_start = self.get_y()
            for cell_val in row:
                self.set_xy(x_start, y_start)
                self.multi_cell(col_width, 5, cell_val, border="LR", align="L")
                x_start += col_width
            self.set_xy(self.l_margin, y_start + max_h)
        self.ln(4)


V1_CONTENT = [
    ("title", "v1-CardioTrack CT-200 Home Blood Pressure Monitor \u2014 Technical & User Manual"),
    ("h1", "1. Device Overview"),
    ("body", "The CardioTrack CT-200 is an oscillometric, upper-arm blood pressure monitor intended for home use by adult users. It measures systolic pressure, diastolic pressure, and pulse rate, and stores up to 200 readings across two user profiles."),
    ("h2", "1.1 Intended Use"),
    ("body", "The CT-200 is intended to non-invasively measure blood pressure and pulse rate in adults with an arm circumference of 22\u201342 cm. It is not intended for use on neonates, infants, or pregnant users, and is not a diagnostic device \u2014 readings should be interpreted by a qualified clinician."),
    ("h2", "1.2 Indications and Contraindications"),
    ("body", "The device should not be used on the arm ipsilateral to a mastectomy, on limbs with an active intravenous line, or on users with severe arrhythmia without clinician guidance, since oscillometric measurement can be unreliable in these cases."),
    ("h1", "2. Physical and Electrical Specifications"),
    ("h2", "2.1 General Specifications"),
    ("table", [
        ["Parameter", "Value"],
        ["Measurement method", "Oscillometric"],
        ["Pressure range", "0\u2013299 mmHg"],
        ["Pulse range", "40\u2013199 bpm"],
        ["Accuracy (pressure)", "\u00b13 mmHg"],
        ["Accuracy (pulse)", "\u00b15%"],
        ["Power source", "4x AA batteries or 6V DC adapter"],
        ["Display", "Backlit LCD"],
    ]),
    ("h3", "2.1.1.1 Battery Life Under Typical Use"),
    ("body", "Under typical use (three measurements per day), four AA alkaline batteries provide approximately 300 measurement cycles before requiring replacement. The device displays a low-battery icon once remaining capacity falls below 15%."),
    ("h2", "2.2 Cuff Specifications"),
    ("body", "The standard cuff supplied with the CT-200 fits arm circumferences of 22\u201332 cm. A separate large cuff (part number CT200-LC) is available for 32\u201342 cm and must be ordered separately; using the standard cuff outside its rated range will produce inaccurate readings."),
    ("h1", "3. Device Operation"),
    ("h2", "3.1 Powering On and Profile Selection"),
    ("body", "Press and hold the power button for one second to power on the device. Use the profile button to select User 1 or User 2 before beginning a measurement; readings are stored against whichever profile is active at the time of measurement."),
    ("h2", "3.2 Cuff Inflation Sequence"),
    ("body", "On starting a measurement, the device inflates the cuff to an initial target of 180 mmHg. If the user's pulse is not detected by 180 mmHg, the device inflates in 40 mmHg increments up to a maximum of 299 mmHg before aborting with an error. Deflation occurs in controlled steps of approximately 3 mmHg to capture oscillometric pulse data."),
    ("h2", "3.4 Auto Shutoff"),
    ("body", "To conserve battery, the CT-200 automatically powers off after 60 seconds of inactivity on the home screen, and after 3 minutes of inactivity if a measurement screen is left open without starting a reading."),
    ("h2", "3.3 Result Display and Classification"),
    ("body", "After a completed measurement, the device displays systolic pressure, diastolic pressure, and pulse rate simultaneously, along with a classification indicator (see 2.1, 4.3 for related specifications and alarm thresholds) based on the most recent joint clinical guidance available at time of manufacture."),
    ("numbered_list", [
        "1. Normal: systolic < 120 and diastolic < 80",
        "2. Elevated: systolic 120\u2013129 and diastolic < 80",
        "3. Hypertension Stage 1: systolic 130\u2013139 or diastolic 80\u201389",
        "4. Hypertension Stage 2: systolic >= 140 or diastolic >= 90",
        "5. Hypertensive Crisis: systolic > 180 or diastolic > 120 \u2014 device recommends seeking immediate medical attention",
    ]),
    ("h1", "4. Alarms and Safety Behavior"),
    ("h2", "4.1 Overpressure Protection"),
    ("body", "If cuff pressure exceeds 299 mmHg at any point, or exceeds 300 mmHg for longer than 3 seconds due to sensor fault, the device immediately triggers an emergency deflation valve, halting inflation and venting the cuff within 2 seconds, independent of the main firmware control loop."),
    ("h2", "4.2 Error Codes"),
    ("table", [
        ["Code", "Meaning", "Device Behavior"],
        ["E1", "Cuff not connected or leak detected", "Aborts measurement, displays E1"],
        ["E2", "Motion artifact detected during measurement", "Aborts measurement, displays E2, prompts retry"],
        ["E3", "Overpressure condition", "Auto-deflates within 2 seconds, displays E3"],
        ["E4", "Low battery during measurement", "Aborts measurement, displays E4"],
        ["E5", "Internal sensor fault", "Device disables measurement function, displays E5 until serviced"],
    ]),
    ("h2", "4.3 Alarm Thresholds"),
    ("body", "The device does not sound an audible alarm for elevated readings by default; audible alarms are limited to the E1\u2013E5 error conditions above and are user-configurable in the settings menu, except for E3 (overpressure), which cannot be silenced for safety reasons."),
    ("h1", "5. Data Management"),
    ("h2", "5.1 Local Storage"),
    ("body", "The CT-200 stores up to 100 readings per user profile in non-volatile memory. When storage is full, the oldest reading for that profile is overwritten automatically; there is no user-facing warning before this occurs."),
    ("h2", "5.2 Bluetooth Sync"),
    ("body", 'The device can pair with the CardioTrack companion app via Bluetooth Low Energy. Readings sync automatically when the app is open and the device is within range; there is no manual "sync now" trigger in firmware version 1.x.'),
    ("h1", "6. Maintenance and Cleaning"),
    ("h2", "6.1 Cleaning Instructions"),
    ("body", "Wipe the device body and cuff exterior with a soft, dry cloth or one lightly dampened with water. Do not submerge the device or cuff, and do not use alcohol, solvents, or abrasive cleaners on the display."),
    ("h2", "6.2 Calibration"),
    ("body", "Anthropic recommends professional recalibration every 2 years or after any drop or significant impact. The device does not perform self-calibration; there is no field calibration procedure available to end users."),
    ("h1", "7. Troubleshooting"),
    ("h2", "7.1 Error Codes"),
    ("body", "If a code from Section 4.2 appears and persists after following the on-screen retry prompt twice, users should discontinue use and contact CardioTrack support rather than attempting further self-diagnosis, particularly for E5, which indicates an internal sensor fault."),
    ("h2", "7.2 Inconsistent Readings"),
    ("body", "Inconsistent readings between measurements are most commonly caused by cuff mispositioning, talking or moving during measurement, or measuring within 30 minutes of exercise, caffeine, or smoking; the manual recommends resting quietly for 5 minutes before remeasuring."),
    ("h1", "8. Regulatory Information"),
    ("h2", "8.1 Classification"),
    ("body", "The CT-200 is classified as a Class II medical device under applicable regulations for non-invasive blood pressure monitors and has been validated against relevant clinical accuracy standards for oscillometric devices."),
]


V2_CONTENT = [
    ("title", "v2-CardioTrack CT-200 Home Blood Pressure Monitor \u2014 Technical & User Manual"),
    ("h1", "1. Device Overview"),
    ("body", "The CardioTrack CT-200 is an oscillometric, upper-arm blood pressure monitor intended for home use by adult users. It measures systolic pressure, diastolic pressure, and pulse rate, and stores up to 200 readings across two user profiles."),
    ("h2", "1.1 Intended Use"),
    ("body", "The CT-200 is intended to non-invasively measure blood pressure and pulse rate in adults with an arm circumference of 22\u201342 cm. It is not intended for use on neonates, infants, or pregnant users, and is not a diagnostic device \u2014 readings should be interpreted by a qualified clinician."),
    ("h2", "1.2 Indications and Contraindications"),
    ("body", "The device should not be used on the arm ipsilateral to a mastectomy, on limbs with an active intravenous line, or on users with severe arrhythmia without clinician guidance, since oscillometric measurement can be unreliable in these cases."),
    ("h1", "2. Physical and Electrical Specifications"),
    ("h2", "2.1 General Specifications"),
    ("table", [
        ["Parameter", "Value"],
        ["Measurement method", "Oscillometric"],
        ["Pressure range", "0\u2013299 mmHg"],
        ["Pulse range", "40\u2013199 bpm"],
        ["Accuracy (pressure)", "\u00b13 mmHg"],
        ["Accuracy (pulse)", "\u00b15%"],
        ["Power source", "4x AA batteries or 6V DC adapter"],
        ["Display", "Backlit LCD"],
    ]),
    ("h3", "2.1.1.1 Battery Life Under Typical Use"),
    ("body", "Under typical use (three measurements per day), four AA alkaline batteries provide approximately 250 measurement cycles before requiring replacement \u2014 revised downward from earlier estimates after extended field testing. The device displays a low-battery icon once remaining capacity falls below 10%."),
    ("h2", "2.2 Cuff Specifications"),
    ("body", "The standard cuff supplied with the CT-200 fits arm circumferences of 22\u201332 cm. A separate large cuff (part number CT200-LC) is available for 32\u201342 cm and must be ordered separately; using the standard cuff outside its rated range will produce inaccurate readings."),
    ("h1", "3. Device Operation"),
    ("h2", "3.1 Powering On and Profile Selection"),
    ("body", "Press and hold the power button for one second to power on the device. Use the profile button to select User 1 or User 2 before beginning a measurement; readings are stored against whichever profile is active at the time of measurement."),
    ("h2", "3.2 Cuff Inflation Sequence"),
    ("body", "On starting a measurement, the device inflates the cuff to an initial target of 180 mmHg. If the user's pulse is not detected by 180 mmHg, the device inflates in 30 mmHg increments up to a maximum of 299 mmHg before aborting with an error. Deflation occurs in controlled steps of approximately 3 mmHg to capture oscillometric pulse data. Increment size was reduced from the original 40 mmHg to improve pulse-detection reliability in field testing."),
    ("h2", "3.4 Auto Shutoff"),
    ("body", "To conserve battery, the CT-200 automatically powers off after 60 seconds of inactivity on the home screen, and after 3 minutes of inactivity if a measurement screen is left open without starting a reading."),
    ("h2", "3.3 Result Display and Classification"),
    ("body", "After a completed measurement, the device displays systolic pressure, diastolic pressure, and pulse rate simultaneously, along with a classification indicator (see 2.1, 4.3 for related specifications and alarm thresholds) based on the most recent joint clinical guidance available at time of manufacture."),
    ("numbered_list", [
        "1. Normal: systolic < 120 and diastolic < 80",
        "2. Elevated: systolic 120\u2013129 and diastolic < 80",
        "3. Hypertension Stage 1: systolic 130\u2013139 or diastolic 80\u201389",
        "4. Hypertension Stage 2: systolic >= 140 or diastolic >= 90",
        "5. Hypertensive Crisis: systolic > 180 or diastolic > 120 \u2014 device recommends seeking immediate medical attention",
    ]),
    ("h1", "4. Alarms and Safety Behavior"),
    ("h2", "4.1 Overpressure Protection"),
    ("body", "If cuff pressure exceeds 299 mmHg at any point, or exceeds 300 mmHg for longer than 3 seconds due to sensor fault, the device immediately triggers an emergency deflation valve, halting inflation and venting the cuff within 2 seconds, independent of the main firmware control loop."),
    ("h2", "4.2 Error Codes"),
    ("table", [
        ["Code", "Meaning", "Device Behavior"],
        ["E1", "Cuff not connected or leak detected", "Aborts measurement, displays E1"],
        ["E2", "Motion artifact detected during measurement", "Aborts measurement, displays E2, prompts retry"],
        ["E3", "Overpressure condition", "Auto-deflates within 1.5 seconds, displays E3"],
        ["E4", "Low battery during measurement", "Aborts measurement, displays E4"],
        ["E5", "Internal sensor fault", "Device disables measurement function, displays E5 until serviced"],
        ["E6", "Bluetooth sync failure", "Displays E6 on next sync attempt; does not affect measurement"],
    ]),
    ("h2", "4.3 Alarm Thresholds"),
    ("body", "The device does not sound an audible alarm for elevated readings by default; audible alarms are limited to the E1\u2013E6 error conditions above and are user-configurable in the settings menu, except for E3 (overpressure), which cannot be silenced for safety reasons."),
    ("h1", "5. Data Management"),
    ("h2", "5.1 Local Storage"),
    ("body", "The CT-200 stores up to 100 readings per user profile in non-volatile memory. When storage is full, the oldest reading for that profile is overwritten automatically; there is no user-facing warning before this occurs."),
    ("h2", "5.2 Bluetooth Sync"),
    ("body", 'The device can pair with the CardioTrack companion app via Bluetooth Low Energy. Readings sync automatically when the app is open and the device is within range; there is no manual "sync now" trigger in firmware version 1.x.'),
    ("h2", "5.3 Data Export"),
    ("body", "Starting with firmware 1.4, the companion app supports exporting stored readings as a CSV file containing timestamp, profile, systolic, diastolic, pulse, and classification columns. Export requires the device to have completed at least one successful Bluetooth sync in the current session."),
    ("h1", "6. Maintenance and Cleaning"),
    ("h2", "6.1 Cleaning Instructions"),
    ("body", "Wipe the device body and cuff exterior with a soft, dry cloth or one lightly dampened with water. Do not submerge the device or cuff, and do not use alcohol, solvents, or abrasive cleaners on the display."),
    ("h2", "6.2 Calibration"),
    ("body", "Anthropic recommends professional recalibration every 2 years or after any drop or significant impact. The device does not perform self-calibration; there is no field calibration procedure available to end users."),
    ("h1", "7. Troubleshooting"),
    ("h2", "7.1 Error Codes"),
    ("body", "If a code from Section 4.2 appears and persists after following the on-screen retry prompt twice, users should discontinue use and contact CardioTrack support rather than attempting further self-diagnosis, particularly for E5, which indicates an internal sensor fault."),
    ("h2", "7.2 Inconsistent Readings"),
    ("body", "Inconsistent readings between measurements are most commonly caused by cuff mispositioning, talking or moving during measurement, or measuring within 30 minutes of exercise, caffeine, or smoking; the manual recommends resting quietly for 5 minutes before remeasuring."),
    ("h1", "8. Regulatory Information"),
    ("h2", "8.1 Classification"),
    ("body", "The CT-200 is classified as a Class II medical device under applicable regulations for non-invasive blood pressure monitors and has been validated against relevant clinical accuracy standards for oscillometric devices."),
]


def build_pdf(version_label, content, output_path):
    pdf = ManualPDF()
    pdf.alias_nb_pages()
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_page()

    for kind, data in content:
        if kind == "title":
            pdf.add_title(data)
        elif kind == "h1":
            pdf.add_h1(data)
        elif kind == "h2":
            pdf.add_h2(data)
        elif kind == "h3":
            pdf.add_h3(data)
        elif kind == "body":
            pdf.add_body(data)
        elif kind == "table":
            pdf.add_table(data[0], data[1:])
        elif kind == "numbered_list":
            for item in data:
                pdf.add_list_item(item)

    pdf.output(output_path)
    print(f"  Created: {output_path}")


if __name__ == "__main__":
    build_pdf("v1", V1_CONTENT, "pdfs/v1-CardioTrack_CT200_Manual.pdf")
    build_pdf("v2", V2_CONTENT, "pdfs/v2-CardioTrack_CT200_Manual.pdf")
    print("PDF generation complete.")
