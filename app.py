from flask import Flask, request, send_file, jsonify
import requests
from bs4 import BeautifulSoup
import csv
import time

app = Flask(__name__)

SEM_MAP = {
    "1st": "I", "2nd": "II", "3rd": "III", "4th": "IV",
    "5th": "V", "6th": "VI", "7th": "VII", "8th": "VIII"
}

def get_exam_held(sem, session):
    odd = ["1st", "3rd", "5th", "7th"]
    if sem in odd:
        return f"July/{int(session) + 1}"
    else:
        return f"November/{session}"

@app.route("/bulk-result", methods=["POST"])
def bulk_result():
    data = request.json

    start_reg = int(data.get("start_reg"))
    end_reg = int(data.get("end_reg"))
    sem = data.get("sem")
    session = data.get("session")

    if not all([start_reg, end_reg, sem, session]):
        return jsonify({"error": "Missing input"}), 400

    sem_roman = SEM_MAP.get(sem)
    exam_held = get_exam_held(sem, session)

    filename = "beu_results_with_marks.csv"

    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Reg No", "Subject Code", "Subject Name", "Marks", "Status"])

        for reg in range(start_reg, end_reg + 1):
            url = (
                f"https://beu-bih.ac.in/result-three?"
                f"name=B.Tech.%20{sem}%20Semester%20Examination,%20{session}"
                f"&semester={sem_roman}"
                f"&session={session}"
                f"&regNo={reg}"
                f"&exam_held={exam_held.replace('/', '%2F')}"
            )

            try:
                r = requests.get(url, timeout=10)
                soup = BeautifulSoup(r.text, "html.parser")

                if "Result not found" in soup.text:
                    print(f"{reg} ❌")
                    continue

                tables = soup.find_all("table")
                if not tables:
                    continue

                rows = tables[-1].find_all("tr")[1:]

                for row in rows:
                    cols = row.find_all("td")
                    if len(cols) < 4:
                        continue

                    writer.writerow([
                        reg,
                        cols[0].get_text(strip=True),
                        cols[1].get_text(strip=True),
                        cols[2].get_text(strip=True),
                        cols[-1].get_text(strip=True)
                    ])

                print(f"{reg} ✔")
                time.sleep(2)

            except Exception as e:
                print(reg, "ERROR", e)

    return send_file(filename, as_attachment=True)

if __name__ == "__main__":
    app.run()
