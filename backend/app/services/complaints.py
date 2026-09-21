"""Complaint drafting — factual, editable drafts from confirmed data only.

Never fabricates agency names, resolution promises, or urgency claims.
Templates are reviewed text in English, Hindi, and Marathi.
"""

from datetime import datetime, timezone

from app.models.report import Report

ISSUE_LABELS = {
    "en": {
        "pothole": "pothole(s) on the road",
        "garbage": "uncollected garbage",
        "damaged_streetlight": "damaged streetlight(s)",
        "waterlogging": "waterlogging on the road",
        "illegal_dumping": "illegal dumping of waste",
    },
    "hi": {
        "pothole": "सड़क पर गड्ढे",
        "garbage": "इकट्ठा न हुआ कचरा",
        "damaged_streetlight": "क्षतिग्रस्त स्ट्रीट लाइट",
        "waterlogging": "सड़क पर जलजमाव",
        "illegal_dumping": "अवैध कचरा डंपिंग",
    },
    "mr": {
        "pothole": "रस्त्यावर खड्डे",
        "garbage": "न घेतलेला कचरा",
        "damaged_streetlight": "खराब झालेला पथदिवा",
        "waterlogging": "रस्त्यावर पाणी साचणे",
        "illegal_dumping": "नक्कीशी विरोधी कचरा फेकणे",
    },
}

TEMPLATES = {
    "en": {
        "subject": "Complaint: {issue_label} at {landmark}",
        "body": (
            "Subject: {issue_label} at {landmark}\n\n"
            "Dear Sir/Madam,\n\n"
            "I would like to report {issue_label} near {landmark} "
            "(approximate location: {coords}).\n\n"
            "Date observed: {date}.\n"
            "Details provided by the reporter: {description}\n\n"
            "Requesting an inspection and necessary action.\n\n"
            "Regards,\n{name}"
        ),
    },
    "hi": {
        "subject": "शिकायत: {landmark} के पास {issue_label}",
        "body": (
            "विषय: {landmark} के पास {issue_label}\n\n"
            "महोदय/महोदया,\n\n"
            "मैं {landmark} के पास {issue_label} की शिकायत दर्ज करना चाहता/चाहती हूँ "
            "(अनुमानित स्थान: {coords})।\n\n"
            "अवलोकन की तिथि: {date}।\n"
            "शिकायतकर्ता द्वारा दिए गए विवरण: {description}\n\n"
            "कृपया निरीक्षण कर आवश्यक कार्रवाई करें।\n\n"
            "सादर,\n{name}"
        ),
    },
    "mr": {
        "subject": "तक्रार: {landmark} जवळ {issue_label}",
        "body": (
            "विषय: {landmark} जवळ {issue_label}\n\n"
            "माननीय अधिकारी,\n\n"
            "मला {landmark} जवळ {issue_label} याची तक्रार नोंदवायची आहे "
            "(अंदाजे स्थान: {coords})।\n\n"
            "निरीक्षणाची तारीख: {date}.\n"
            "तक्रारदाराने दिलेला तपशील: {description}\n\n"
            "कृपया तपासणी करून आवश्यक ती कार्यवाही करावी.\n\n"
            "धन्यवाद,\n{name}"
        ),
    },
}


def draft_complaint(report: Report, reporter_name: str | None, language: str = "en") -> dict:
    """Build a complaint draft strictly from confirmed report fields."""
    lang = language if language in TEMPLATES else "en"
    labels = ISSUE_LABELS[lang]
    tpl = TEMPLATES[lang]

    issue_label = labels.get(report.issue_type, labels["pothole"])
    landmark = report.landmark or "the reported location"
    if lang == "en":
        landmark_phrase = landmark
    else:
        landmark_phrase = landmark  # landmark names stay as provided

    coords = "not disclosed"
    if report.public_latitude is not None and report.public_longitude is not None:
        coords = f"{report.public_latitude:.3f}, {report.public_longitude:.3f}"

    observed = report.occurred_at or report.submitted_at or datetime.now(timezone.utc)
    date_str = observed.strftime("%d %B %Y")

    description = (report.description or "").strip()
    if lang == "en":
        description = description or "No additional details provided."
    elif lang == "hi":
        description = description or "कोई अतिरिक्त विवरण नहीं दिया गया।"
    else:
        description = description or "अतिरिक्त तपशील दिला गेला नाही."

    name = (reporter_name or "").strip()
    if lang == "en":
        name = name or "[Your name]"
    elif lang == "hi":
        name = name or "[आपका नाम]"
    else:
        name = name or "[तुमचे नाव]"

    subject = tpl["subject"].format(issue_label=issue_label, landmark=landmark_phrase)
    body = tpl["body"].format(
        issue_label=issue_label,
        landmark=landmark_phrase,
        coords=coords,
        date=date_str,
        description=description,
        name=name,
    )
    return {"subject": subject, "body": body}
