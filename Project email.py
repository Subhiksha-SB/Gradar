import csv
import smtplib
from email.message import EmailMessage

SUBJECTS = ["Tamil", "English", "Maths", "Science", "Social Science"]

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
        
        marks = []
        for sub in SUBJECTS:
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
            "average": avg
        })

    return students

def assign_ranks(students):
    sorted_students = sorted(students, key=lambda x: x["total"], reverse=True)
    for rank, student in enumerate(sorted_students, start=1):
        student["rank"] = rank
    return sorted_students

def display_results(students):
    print("\n" + "="*85)
    print(f"{'Rank':<6}{'Name':<20}{'Tamil':<8}{'English':<8}{'Maths':<8}{'Science':<8}{'Social':<8}{'Total':<8}{'Average':<8}")
    print("="*85)
    for s in students:
        marks = s["marks"]
        print(f"#{s['rank']:<5}{s['name']:<20}{marks[0]:<8}{marks[1]:<8}{marks[2]:<8}{marks[3]:<8}{marks[4]:<8}{s['total']:<8}{s['average']:<8.2f}")
    print("="*85)

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
        writer.writerow(["Rank", "Name", "Tamil", "English", "Maths", "Science", "Social Science", "Total", "Average", "Parent Email"])
        for s in students:
            writer.writerow([
                s['rank'],
                s['name'],
                s['marks'][0],
                s['marks'][1],
                s['marks'][2],
                s['marks'][3],
                s['marks'][4],
                s['total'],
                f"{s['average']:.2f}",
                s['parent_email']
            ])
    print(f"\n✅ Results saved successfully in '{filename}'")

def send_emails(students, sender_email, sender_password):
    try:
        server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
        server.login(sender_email, sender_password)

        for s in students:
            msg = EmailMessage()
            msg["Subject"] = f"📊 Report Card for {s['name']}"
            msg["From"] = sender_email
            msg["To"] = s["parent_email"]

            # HTML formatted email body (premium feel!)
            html_body = f"""
            <html>
            <body style="font-family: Arial, sans-serif; color: #333;">
                <h2 style="color: #4A5568;">Student Academic Report</h2>
                <p>Dear Parent,</p>
                <p>Here is the official academic report card for <strong>{s['name']}</strong>:</p>
                <table style="border-collapse: collapse; width: 100%; max-width: 500px; margin: 15px 0;">
                    <tr style="background-color: #F7FAFC;">
                        <th style="border: 1px solid #E2E8F0; padding: 8px; text-align: left;">Subject</th>
                        <th style="border: 1px solid #E2E8F0; padding: 8px; text-align: center;">Marks</th>
                    </tr>
                    <tr>
                        <td style="border: 1px solid #E2E8F0; padding: 8px;">Tamil</td>
                        <td style="border: 1px solid #E2E8F0; padding: 8px; text-align: center;">{s['marks'][0]}</td>
                    </tr>
                    <tr>
                        <td style="border: 1px solid #E2E8F0; padding: 8px;">English</td>
                        <td style="border: 1px solid #E2E8F0; padding: 8px; text-align: center;">{s['marks'][1]}</td>
                    </tr>
                    <tr>
                        <td style="border: 1px solid #E2E8F0; padding: 8px;">Maths</td>
                        <td style="border: 1px solid #E2E8F0; padding: 8px; text-align: center;">{s['marks'][2]}</td>
                    </tr>
                    <tr>
                        <td style="border: 1px solid #E2E8F0; padding: 8px;">Science</td>
                        <td style="border: 1px solid #E2E8F0; padding: 8px; text-align: center;">{s['marks'][3]}</td>
                    </tr>
                    <tr>
                        <td style="border: 1px solid #E2E8F0; padding: 8px;">Social Science</td>
                        <td style="border: 1px solid #E2E8F0; padding: 8px; text-align: center;">{s['marks'][4]}</td>
                    </tr>
                    <tr style="font-weight: bold; background-color: #EDF2F7;">
                        <td style="border: 1px solid #E2E8F0; padding: 8px;">Total Score</td>
                        <td style="border: 1px solid #E2E8F0; padding: 8px; text-align: center;">{s['total']} / 500</td>
                    </tr>
                    <tr style="font-weight: bold; background-color: #E2E8F0;">
                        <td style="border: 1px solid #E2E8F0; padding: 8px;">Class Rank</td>
                        <td style="border: 1px solid #E2E8F0; padding: 8px; text-align: center;">#{s['rank']}</td>
                    </tr>
                </table>
                <p>Child's Average Score: <strong>{s['average']:.2f}%</strong></p>
                <br>
                <p>Regards,</p>
                <p><strong>Class Teacher</strong></p>
            </body>
            </html>
            """
            msg.add_alternative(html_body, subtype="html")

            server.send_message(msg)
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
