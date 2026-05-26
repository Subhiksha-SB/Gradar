import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage

# Subject names — must match order marks are stored
SUBJECT_NAMES = ["Tamil", "English", "Maths", "Science", "Social Science"]
SUBJECT_ICONS = ["📖", "📝", "🔢", "🔬", "🌍"]


def _grade_label(avg: float) -> str:
    if avg >= 90: return "Outstanding 🌟"
    if avg >= 75: return "Excellent ⭐"
    if avg >= 60: return "Good 👍"
    if avg >= 50: return "Satisfactory 📚"
    return "Needs Improvement 💪"


def _build_html_body(student: dict) -> str:
    """Build a rich HTML email body."""
    marks       = student["marks"]
    total_max   = len(marks) * 100
    avg         = student["average"]
    grade_label = _grade_label(avg)

    # Progress bar colour
    bar_colour = (
        "#48bb78" if avg >= 75 else
        "#63b3ed" if avg >= 60 else
        "#f6ad55" if avg >= 50 else
        "#fc8181"
    )

    # Build subject rows
    subject_rows = ""
    for name, icon, mark in zip(SUBJECT_NAMES, SUBJECT_ICONS, marks):
        pct   = mark  # out of 100
        s_clr = "#48bb78" if pct >= 75 else "#f6ad55" if pct >= 50 else "#fc8181"
        subject_rows += f"""
        <tr>
          <td style="padding:10px 14px;border-bottom:1px solid #2d3748;color:#a0aec0;font-size:13px;">
            {icon} {name}
          </td>
          <td style="padding:10px 14px;border-bottom:1px solid #2d3748;text-align:right;">
            <span style="background:{s_clr}22;color:{s_clr};
                         border:1px solid {s_clr}44;border-radius:20px;
                         padding:3px 12px;font-weight:700;font-family:monospace;font-size:13px;">
              {mark} / 100
            </span>
          </td>
        </tr>"""

    return f"""
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width,initial-scale=1.0"/>
  <title>Report Card — {student['name']}</title>
  <style>
    @keyframes shine {{
      0% {{ left: -100%; }}
      30% {{ left: 150%; }}
      100% {{ left: 150%; }}
    }}
    .brand-logo-container {{
      position: relative;
      width: 56px;
      height: 56px;
      border-radius: 14px;
      overflow: hidden;
      display: inline-block;
      background: radial-gradient(circle at 40% 40%, rgba(99,179,237,0.15), rgba(15,22,35,0.8));
      border: 1px solid rgba(255,255,255,0.12);
      margin-bottom: 12px;
      box-shadow: 0 0 20px rgba(99,179,237,0.25);
    }}
    .brand-logo-img {{
      width: 100%;
      height: 100%;
      object-fit: cover;
      display: block;
    }}
    .shine-sweep {{
      position: absolute;
      top: 0;
      left: -100%;
      width: 50%;
      height: 100%;
      background: linear-gradient(
        90deg,
        rgba(255, 255, 255, 0) 0%,
        rgba(255, 255, 255, 0.45) 50%,
        rgba(255, 255, 255, 0) 100%
      );
      transform: skewX(-25deg);
      animation: shine 3.5s infinite ease-in-out;
    }}
  </style>
</head>
<body style="margin:0;padding:0;background:#05070f;font-family:'Segoe UI',Arial,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0"
         style="background:#05070f;padding:32px 16px;">
    <tr><td align="center">
      <table width="600" cellpadding="0" cellspacing="0"
             style="background:#0c0f1e;border-radius:16px;overflow:hidden;
                    border:1px solid rgba(255,255,255,0.08);max-width:600px;width:100%;box-shadow: 0 4px 24px rgba(0,0,0,0.4);">

        <!-- Header -->
        <tr>
          <td style="background: linear-gradient(135deg, #1a1f3a 0%, #0d1117 50%, #0f1623 100%);
                     padding:36px 36px;text-align:center;border-bottom: 1px solid rgba(255,255,255,0.08);">
            <div class="brand-logo-container">
              <img src="cid:gradar_logo" class="brand-logo-img" alt="Gradar Logo"/>
              <div class="shine-sweep"></div>
            </div>
            <h1 style="margin:0;font-size:24px;font-weight:800;color:#f0f4ff;
                        letter-spacing:-0.5px;">Gradar</h1>
            <p style="margin:6px 0 0;color:#63b3ed;font-size:13px;font-weight:500;
                       text-transform:uppercase;letter-spacing:1px;">
              Academic Performance Report
            </p>
          </td>
        </tr>

        <!-- Student info -->
        <tr>
          <td style="padding:28px 36px 16px;">
            <p style="margin:0 0 4px;color:#718096;font-size:12px;text-transform:uppercase;
                       letter-spacing:1px;font-weight:600;">Dear Parent,</p>
            <p style="margin:0;color:#e2e8f0;font-size:15px;line-height:1.6;">
              Here is the academic performance report for your child
              <strong style="color:#63b3ed;">{student['name']}</strong>.
            </p>
          </td>
        </tr>

        <!-- Summary cards -->
        <tr>
          <td style="padding:0 36px 20px;">
            <table width="100%" cellpadding="0" cellspacing="0">
              <tr>
                <td width="32%" style="padding-right:8px;">
                  <div style="background:#1a2744;border:1px solid #2d3748;border-radius:12px;
                               padding:16px;text-align:center;">
                    <div style="font-size:24px;font-weight:800;color:#f0f4ff;
                                 font-family:monospace;">{student['total']}</div>
                    <div style="font-size:11px;color:#718096;text-transform:uppercase;
                                 letter-spacing:0.8px;margin-top:4px;">Total / {total_max}</div>
                  </div>
                </td>
                <td width="32%" style="padding-right:8px;">
                  <div style="background:#1a2744;border:1px solid #2d3748;border-radius:12px;
                               padding:16px;text-align:center;">
                    <div style="font-size:24px;font-weight:800;color:{bar_colour};
                                 font-family:monospace;">{avg:.1f}%</div>
                    <div style="font-size:11px;color:#718096;text-transform:uppercase;
                                 letter-spacing:0.8px;margin-top:4px;">Average</div>
                  </div>
                </td>
                <td width="32%">
                  <div style="background:#1a2744;border:1px solid #2d3748;border-radius:12px;
                               padding:16px;text-align:center;">
                    <div style="font-size:24px;font-weight:800;color:#9f7aea;
                                 font-family:monospace;">#{student['rank']}</div>
                    <div style="font-size:11px;color:#718096;text-transform:uppercase;
                                 letter-spacing:0.8px;margin-top:4px;">Class Rank</div>
                  </div>
                </td>
              </tr>
            </table>
          </td>
        </tr>

        <!-- Average bar -->
        <tr>
          <td style="padding:0 36px 24px;">
            <div style="background:#1a2744;border:1px solid #2d3748;border-radius:12px;padding:16px 20px;">
              <div style="display:flex;justify-content:space-between;margin-bottom:10px;">
                <span style="color:#718096;font-size:12px;font-weight:600;text-transform:uppercase;
                              letter-spacing:0.8px;">Overall Performance</span>
                <span style="color:{bar_colour};font-size:12px;font-weight:700;">{grade_label}</span>
              </div>
              <div style="background:#2d3748;border-radius:6px;height:8px;overflow:hidden;">
                <div style="background:{bar_colour};width:{avg}%;height:100%;border-radius:6px;"></div>
              </div>
            </div>
          </td>
        </tr>

        <!-- Subject marks table -->
        <tr>
          <td style="padding:0 36px 28px;">
            <p style="margin:0 0 12px;color:#718096;font-size:12px;text-transform:uppercase;
                       letter-spacing:1px;font-weight:600;">Subject-wise Marks</p>
            <table width="100%" cellpadding="0" cellspacing="0"
                   style="background:#1a2744;border:1px solid #2d3748;border-radius:12px;overflow:hidden;">
              <thead>
                <tr style="background:#0d1626;">
                  <th style="padding:10px 14px;text-align:left;color:#4a5568;font-size:11px;
                              text-transform:uppercase;letter-spacing:0.8px;font-weight:600;">Subject</th>
                  <th style="padding:10px 14px;text-align:right;color:#4a5568;font-size:11px;
                              text-transform:uppercase;letter-spacing:0.8px;font-weight:600;">Marks</th>
                </tr>
              </thead>
              <tbody>{subject_rows}
              </tbody>
            </table>
          </td>
        </tr>

        <!-- Message -->
        <tr>
          <td style="padding:0 36px 28px;">
            <div style="background:#1a2744;border-left:3px solid #63b3ed;border-radius:8px;
                         padding:14px 18px;">
              <p style="margin:0;color:#a0aec0;font-size:13px;line-height:1.7;">
                We encourage you to discuss these results with your child and
                support their continued learning journey. Please feel free to
                reach out to the class teacher for any queries.
              </p>
            </div>
          </td>
        </tr>

        <!-- Footer -->
        <tr>
          <td style="background:#05070f;border-top:1px solid rgba(255,255,255,0.08);padding:20px 36px;text-align:center;">
            <p style="margin:0;color:#475569;font-size:12px;">
              Sent by <strong style="color:#63b3ed;">Gradar</strong> &nbsp;·&nbsp; Class Teacher
            </p>
          </td>
        </tr>

      </table>
    </td></tr>
  </table>
</body>
</html>"""


def _build_plain_text(student: dict) -> str:
    """Plain-text fallback."""
    marks     = student["marks"]
    total_max = len(marks) * 100
    lines     = "\n".join(
        f"  {name:<18}: {mark:>3} / 100"
        for name, mark in zip(SUBJECT_NAMES, marks)
    )
    divider = "  " + "-" * 28
    return f"""\
Dear Parent,

Here is the academic performance report for {student['name']}:

  SUBJECT-WISE MARKS
{divider}
{lines}
{divider}
  Total Score   : {student['total']} / {total_max}
  Average Score : {student['average']:.1f}%
  Class Rank    : #{student['rank']}

  Grade         : {_grade_label(student['average'])}

We encourage you to discuss these results with your child.

Warm regards,
Class Teacher (Gradar)
"""


def verify_credentials(sender_email: str, sender_password: str) -> dict:
    """
    Test Gmail login only (does NOT send any email).
    Returns {success, message}.
    """
    try:
        ctx = ssl.create_default_context()
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=ctx) as server:
            server.login(sender_email, sender_password)
        return {"success": True, "message": "Credentials verified successfully!"}
    except smtplib.SMTPAuthenticationError:
        return {"success": False,
                "message": "Authentication failed. Make sure you are using a Gmail App Password, not your normal password."}
    except Exception as exc:
        return {"success": False, "message": f"Connection error: {exc}"}


def send_report_email(student: dict,
                      sender_email: str,
                      sender_password: str) -> dict:
    """
    Send a rich HTML report card email to the student's parent.
    From: teacher's Gmail
    To  : student['parent_email']
    """
    try:
        # Build multipart message (using "related" to support inline logo)
        msg = MIMEMultipart("related")
        msg["Subject"] = f"📊 Report Card — {student['name']} | Gradar"
        msg["From"]    = f"Gradar <{sender_email}>"
        msg["To"]      = student["parent_email"]

        # Create alternative part for plain text & HTML
        msg_alternative = MIMEMultipart("alternative")
        msg.attach(msg_alternative)

        # Attach plain text first, then HTML (email clients prefer last)
        msg_alternative.attach(MIMEText(_build_plain_text(student), "plain", "utf-8"))
        msg_alternative.attach(MIMEText(_build_html_body(student),  "html",  "utf-8"))

        # Attach logo as inline image
        import os
        logo_path = os.path.join(os.path.dirname(__file__), "..", "frontend", "gradar-logo.png")
        if os.path.exists(logo_path):
            with open(logo_path, "rb") as f:
                img_data = f.read()
            img = MIMEImage(img_data)
            img.add_header("Content-ID", "<gradar_logo>")
            img.add_header("Content-Disposition", "inline", filename="gradar-logo.png")
            msg.attach(img)

        ctx = ssl.create_default_context()
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=ctx) as server:
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, student["parent_email"], msg.as_string())

        return {
            "success": True,
            "message": f"Report card sent to {student['parent_email']}"
        }

    except smtplib.SMTPAuthenticationError:
        return {"success": False,
                "message": "Authentication failed — use a Gmail App Password, not your normal password."}
    except smtplib.SMTPRecipientsRefused:
        return {"success": False,
                "message": f"Recipient address rejected: {student['parent_email']}"}
    except smtplib.SMTPException as exc:
        return {"success": False, "message": f"SMTP error: {exc}"}
    except Exception as exc:
        return {"success": False, "message": f"Unexpected error: {exc}"}
