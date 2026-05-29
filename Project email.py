import csv
import smtplib
from email.message import EmailMessage

def get_subjects_for_class(grade: str, group: str = None) -> list:
    if grade in ["11", "12"]:
        if group == "Biology":
            return ["Tamil / French", "English", "Maths", "Physics", "Chemistry", "Biology"]
        elif group == "Computer":
            return ["Tamil / French", "English", "Maths", "Physics", "Chemistry", "Computer Science"]
        elif group == "Commerce":
            return ["Tamil / French", "English", "Accountancy", "Commerce", "Economics", "Business Maths / Computer Application"]
    return ["Tamil", "English", "Maths", "Science", "Social Science"]

def get_icons_for_class(grade: str, group: str = None) -> list:
    if grade in ["11", "12"]:
        if group == "Biology":
            return ["🔤", "🔠", "🔢", "⚡", "🧪", "🌿"]
        elif group == "Computer":
            return ["🔤", "🔠", "🔢", "⚡", "🧪", "💻"]
        elif group == "Commerce":
            return ["🔤", "🔠", "📈", "💼", "📊", "🧮"]
    return ["🔤", "🔠", "🔢", "🔬", "🌍"]

def get_student_data():
    students = []
    while True:
        try:
            n = int(input("Enter number of students to add: "))
            if n > 0:
                break
            print("Please enter a number greater than 0.")
        except ValueError:
            print("Invalid input. Please enter a valid number.")

    for i in range(n):
        print(f"\nEnter details for Student {i+1}")
        name = input("Name: ").strip()
        while not name:
            name = input("Name cannot be empty. Enter Name: ").strip()
            
        parent_email = input("Parent Email: ").strip()
        while "@" not in parent_email or "." not in parent_email:
            parent_email = input("Invalid email. Enter Parent Email: ").strip()

        while True:
            grade = input("Class / Grade (1-12): ").strip()
            if grade.isdigit() and 1 <= int(grade) <= 12:
                break
            print("Invalid Class. Please enter a number between 1 and 12.")

        group = None
        if grade in ["11", "12"]:
            while True:
                print("Select Group:")
                print("1. Biology Group")
                print("2. Computer Group")
                print("3. Commerce Group")
                gp_choice = input("Enter choice (1-3): ").strip()
                if gp_choice == "1":
                    group = "Biology"
                    break
                elif gp_choice == "2":
                    group = "Computer"
                    break
                elif gp_choice == "3":
                    group = "Commerce"
                    break
                print("Invalid choice. Please enter 1, 2, or 3.")
        
        active_subs = get_subjects_for_class(grade, group)
        marks = []
        for sub in active_subs:
            while True:
                try:
                    mark = int(input(f"  Enter marks for {sub} (0-100): "))
                    if 0 <= mark <= 100:
                        marks.append(mark)
                        break
                    print("Marks must be between 0 and 100.")
                except ValueError:
                    print("Invalid input. Enter a number between 0 and 100.")

        total = sum(marks)
        avg = total / len(marks)

        students.append({
            "name": name,
            "parent_email": parent_email,
            "marks": marks,
            "total": total,
            "average": avg,
            "grade": grade,
            "group": group
        })

    return students

def assign_ranks(students):
    sorted_students = sorted(students, key=lambda x: x["total"], reverse=True)
    for rank, student in enumerate(sorted_students, start=1):
        student["rank"] = rank
    return sorted_students

def display_results(students):
    print("\n" + "="*95)
    print(f"{'Rank':<6}{'Name':<20}{'Class/Group':<25}{'Total Score':<15}{'Average':<10}")
    print("="*95)
    for s in students:
        class_str = f"Class {s.get('grade', '10')}"
        if s.get('group'):
            class_str += f" ({s.get('group')})"
        
        total_max = len(s['marks']) * 100
        total_str = f"{s['total']} / {total_max}"
        
        print(f"#{s['rank']:<5}{s['name']:<20}{class_str:<25}{total_str:<15}{s['average']:<10.2f}%")
        
        active_subs = get_subjects_for_class(s.get('grade', '10'), s.get('group'))
        sub_marks_str = ", ".join(f"{sub}: {mark}" for sub, mark in zip(active_subs, s['marks']))
        print(f"      📚 Marks: {sub_marks_str}")
        print("-"*95)

def class_summary(students):
    print("\n--- Class Summary ---")
    ranges = {"Outstanding (90-100)": 0, "Excellent (80-89)": 0, "Good (70-79)": 0, "Needs Improvement (Below 70)": 0}
    
    for s in students:
        avg = s["average"]
        if 90 <= avg <= 100:
            ranges["Outstanding (90-100)"] += 1
        elif 80 <= avg < 90:
            ranges["Excellent (80-89)"] += 1
        elif 70 <= avg < 80:
            ranges["Good (70-79)"] += 1
        else:
            ranges["Needs Improvement (Below 70)"] += 1

    for r, count in ranges.items():
        print(f"Students in {r}: {count}")

def save_to_csv(students, filename="results.csv"):
    with open(filename, mode="w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["Rank", "Name", "Class", "Group", "Marks", "Total", "Average", "Parent Email"])
        for s in students:
            writer.writerow([
                s['rank'],
                s['name'],
                s.get('grade', '10'),
                s.get('group', '—'),
                " | ".join(str(m) for m in s['marks']),
                s['total'],
                f"{s['average']:.2f}",
                s['parent_email']
            ])
    print(f"\n✅ Results saved successfully in '{filename}'")

def send_emails(students, sender_email, sender_password):
    import ssl
    import os
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText
    from email.mime.image import MIMEImage

    subject_icons = ["📖", "📝", "🔢", "🔬", "🌍"]

    def grade_label(avg):
        if avg >= 90: return "Outstanding 🌟"
        if avg >= 75: return "Excellent ⭐"
        if avg >= 60: return "Good 👍"
        if avg >= 50: return "Satisfactory 📚"
        return "Needs Improvement 💪"

    def build_plain_text(student):
        marks     = student["marks"]
        total_max = len(marks) * 100
        active_subs = get_subjects_for_class(student.get('grade', '10'), student.get('group'))
        lines     = "\n".join(
            f"  {name:<18}: {mark:>3} / 100"
            for name, mark in zip(active_subs, marks)
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

  Grade         : {grade_label(student['average'])}

We encourage you to discuss these results with your child.

Warm regards,
Class Teacher (AcaTier)
"""

    def build_html_body(student):
        marks       = student["marks"]
        total_max   = len(marks) * 100
        avg         = student["average"]
        g_lbl       = grade_label(avg)

        # Progress bar colour
        bar_colour = (
            "#48bb78" if avg >= 75 else
            "#63b3ed" if avg >= 60 else
            "#f6ad55" if avg >= 50 else
            "#fc8181"
        )

        # Build subject rows
        active_subs = get_subjects_for_class(student.get('grade', '10'), student.get('group'))
        active_icons = get_icons_for_class(student.get('grade', '10'), student.get('group'))
        subject_rows = ""
        for name, icon, mark in zip(active_subs, active_icons, marks):
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
              <img src="cid:acatier_logo" class="brand-logo-img" alt="AcaTier Logo"/>
              <div class="shine-sweep"></div>
            </div>
            <h1 style="margin:0;font-size:24px;font-weight:800;color:#f0f4ff;
                        letter-spacing:-0.5px;">AcaTier</h1>
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
                <span style="color:{bar_colour};font-size:12px;font-weight:700;">{g_lbl}</span>
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
              Sent by <strong style="color:#63b3ed;">AcaTier</strong> &nbsp;·&nbsp; Class Teacher
            </p>
          </td>
        </tr>

      </table>
    </td></tr>
  </table>
</body>
</html>
"""

    try:
        ctx = ssl.create_default_context()
        server = smtplib.SMTP_SSL("smtp.gmail.com", 465, context=ctx)
        server.login(sender_email, sender_password)

        for s in students:
            msg = MIMEMultipart("related")
            class_lbl = f"Class {s.get('grade', '10')}"
            if s.get('group'):
                class_lbl += f" ({s.get('group')} Group)"
            msg["Subject"] = f"📊 Report Card — {s['name']} | {class_lbl} | AcaTier"
            msg["From"]    = f"AcaTier <{sender_email}>"
            msg["To"]      = s["parent_email"]

            msg_alternative = MIMEMultipart("alternative")
            msg.attach(msg_alternative)

            msg_alternative.attach(MIMEText(build_plain_text(s), "plain", "utf-8"))
            msg_alternative.attach(MIMEText(build_html_body(s), "html", "utf-8"))

            logo_path = os.path.join(os.path.dirname(__file__), "student-report-app", "frontend", "acatier-logo.png")
            if os.path.exists(logo_path):
                with open(logo_path, "rb") as f:
                    img_data = f.read()
                img = MIMEImage(img_data)
                img.add_header("Content-ID", "<acatier_logo>")
                img.add_header("Content-Disposition", "inline", filename="acatier-logo.png")
                msg.attach(img)

            server.sendmail(sender_email, s["parent_email"], msg.as_string())
            print(f"✅ Email successfully sent to parent: {s['parent_email']} for {s['name']}")

        server.quit()
        print("\nAll emails dispatched successfully!")

    except Exception as e:
        print("\n❌ Error sending emails. Make sure your Gmail App Password and Address are valid:", e)

def main():
    print("="*60)
    print("🎓 REPORT CARD & SMTP NOTIFICATION TERMINAL SYSTEM 🎓")
    print("="*60)
    print("\n💡 NOTE: We have also built a premium WEB DASHBOARD inside the")
    print("   'student-report-app' folder! To open the web version, run:")
    print("   1. In backend/ run: python app.py")
    print("   2. Open frontend/index.html in your browser")
    print("="*60 + "\n")

    students = []
    
    while True:
        print("\n--- MENU ---")
        print("1. Add Students")
        print("2. Display Leaderboard & Ranks")
        print("3. Delete a Student Record")
        print("4. Save Results to CSV")
        print("5. Send Report Cards via Email")
        print("6. Exit")
        
        choice = input("\nEnter choice (1-6): ").strip()
        
        if choice == "1":
            new_students = get_student_data()
            students.extend(new_students)
            students = assign_ranks(students)
            print(f"\nSuccessfully added {len(new_students)} student(s).")
            
        elif choice == "2":
            if not students:
                print("\n⚠️ No student records. Please add students first.")
                continue
            students = assign_ranks(students)
            display_results(students)
            class_summary(students)
            
        elif choice == "3":
            if not students:
                print("\n⚠️ No student records to delete.")
                continue
            students = assign_ranks(students)
            display_results(students)
            name_to_del = input("\nEnter the student name to delete: ").strip()
            found = False
            for s in students:
                if s["name"].lower() == name_to_del.lower():
                    students.remove(s)
                    found = True
                    print(f"\n🗑️ Record for {s['name']} has been deleted.")
                    break
            if found:
                students = assign_ranks(students)
            else:
                print(f"\n❌ Student named '{name_to_del}' not found.")
                
        elif choice == "4":
            if not students:
                print("\n⚠️ No records to save. Please add students first.")
                continue
            filename = input("\nEnter filename to save (default: results.csv): ").strip()
            if not filename:
                filename = "results.csv"
            save_to_csv(students, filename)
            
        elif choice == "5":
            if not students:
                print("\n⚠️ No student records. Please add students first.")
                continue
            print("\n--- Gmail SMTP Setup ---")
            sender_email = input("Enter your Gmail address: ").strip()
            sender_password = input("Enter Gmail App Password: ").strip()
            if not sender_email or not sender_password:
                print("\n❌ Email and App Password cannot be empty.")
                continue
            print("\nSending report cards...")
            send_emails(students, sender_email, sender_password)
            
        elif choice == "6":
            print("\nExiting program. Goodbye!")
            break
        else:
            print("\n❌ Invalid choice. Please enter a number between 1 and 6.")

if __name__ == "__main__":
    main()
