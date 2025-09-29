#!/usr/bin/env python3
"""
Fetch Google Classroom coursework and write a simple text file for Conky.
Run once (writes $HOME/classroom/classroom.txt). Designed to be invoked by:
  $HOME/classroom/venv/bin/python $HOME/classroom/fetch_assignments.py
"""
import os, pickle, datetime, sys
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

HOME = os.path.expanduser("~")
CREDENTIALS = os.path.join(HOME, "classroom", "credentials.json")
TOKEN = os.path.join(HOME, "classroom", "token.pickle")
OUTPUT = os.path.join(HOME, "classroom", "classroom.txt")

SCOPES = [
    "https://www.googleapis.com/auth/classroom.courses.readonly",
    "https://www.googleapis.com/auth/classroom.coursework.me",
    "https://www.googleapis.com/auth/classroom.courseworkmaterials.readonly"
]

def auth():
    creds = None
    if os.path.exists(TOKEN):
        with open(TOKEN, "rb") as f:
            creds = pickle.load(f)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN, "wb") as f:
            pickle.dump(creds, f)
    return creds

def format_date(d):
    return d.strftime("%b %d, %Y")

def main():
    try:
        creds = auth()
        service = build("classroom", "v1", credentials=creds, cache_discovery=False)

        # list active courses
        courses = []
        page_token = None
        while True:
            res = service.courses().list(pageSize=100, pageToken=page_token, courseStates=["ACTIVE"]).execute()
            courses.extend(res.get("courses", []))
            page_token = res.get("nextPageToken")
            if not page_token:
                break

        assignments = []
        today = datetime.date.today()

        for course in courses:
            course_name = course.get("name", "Unnamed Course")
            try:
                cw_res = service.courses().courseWork().list(courseId=course["id"], pageSize=200).execute()
            except HttpError:
                continue
            items = cw_res.get("courseWork", [])
            for item in items:
                title = item.get("title", "Untitled")
                due = None
                if "dueDate" in item:
                    dd = item["dueDate"]
                    try:
                        due = datetime.date(dd["year"], dd["month"], dd["day"])
                    except Exception:
                        due = None
                # compute status
                if due:
                    delta = (due - today).days
                    if delta < 0:
                        status = f"OVERDUE (was {format_date(due)})"
                    elif delta == 0:
                        status = "Due TODAY"
                    elif delta <= 3:
                        status = f"Due in {delta} day{'s' if delta!=1 else ''} ({format_date(due)})"
                    else:
                        status = f"Due {format_date(due)}"
                else:
                    status = "No due date"

                assignments.append({
                    "course": course_name,
                    "title": title,
                    "due": due,
                    "status": status
                })

        # sort: nearest due dates first; items without due date go last
        assignments.sort(key=lambda a: (a["due"] is None, a["due"] or datetime.date.max))

        # filter out overdue ones
        upcoming = [a for a in assignments if not a['status'].startswith("OVERDUE")]

        # write file
        with open(OUTPUT, "w", encoding="utf-8") as f:
            f.write(f"📚 Google Classroom    (Last update: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')})\n\n")
            if not upcoming:
                f.write("✅ No upcoming assignments.\n")
            else:
                for a in upcoming:
                    f.write(f"- {a['course']}: {a['title']} — {a['status']}\n")

    except Exception as e:
        with open(OUTPUT, "w", encoding="utf-8") as f:
            f.write("⚠️ Error fetching Classroom data\n")
            f.write(str(e) + "\n")
        raise

if __name__ == "__main__":
    main()
