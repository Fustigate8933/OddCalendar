from bs4 import BeautifulSoup
from ics import Calendar, Event
from datetime import datetime
from fastapi import Response, FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from pydantic import BaseModel
import pytz

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

TIMEZONE = pytz.timezone("America/Toronto")

def gen_calendar(source, out_path="odyssey_schedule.ics"):
    soup = BeautifulSoup(source, "html.parser")

    exam = []
    time = []
    room = []
    seat = []

    rows = soup.find_all("tr")[1:]
    for row in rows:
        contents = [content.get_text() for content in row.find_all("td")]
        exam.append(contents[0])
        
        year, interval = contents[2].split()
        start, end = interval.split("–")
        start_time = datetime.strptime(f"{year} {start}", "%Y-%m-%d %H:%M")
        end_time = datetime.strptime(f"{year} {end}", "%Y-%m-%d %H:%M")
        start_time = TIMEZONE.localize(start_time)
        end_time = TIMEZONE.localize(end_time)

        time.append((start_time, end_time))
        room.append(contents[3])
        seat.append(contents[4])

    cal = Calendar()
    for i in range(len(exam)):
        event = Event(
            name=exam[i],
            begin=time[i][0].isoformat(),
            end=time[i][1].isoformat(),
            description=f"Room: {room[i]}, Seat: {seat[i]}"
        )
        cal.events.add(event)

    with open(out_path, "w") as f:
        f.write(cal.serialize())

    return out_path


class HTMLSource(BaseModel):
    html: str

@app.post("/download-calendar")
def download_calendar(request: HTMLSource):
    ics_file = gen_calendar(request.html)

    with open(ics_file, "r") as f:
        ics_content = f.read()

    os.remove(ics_file)

    return Response(content=ics_content, media_type="text/calendar", headers={"Content-Disposition": "attachment; filename=odyssey_schedule.ics"})

