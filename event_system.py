import http.server
import socketserver
import json
from urllib.parse import parse_qs, urlparse

# Data Models
class Event:
    def __init__(self, name, description, date, capacity):
        self.name = name
        self.description = description
        self.date = date
        self.capacity = capacity
        self.participants = []

class Participant:
    def __init__(self, name, roll_number, department):
        self.name = name
        self.roll_number = roll_number
        self.department = department
        self.events = []

# Event Manager
class EventManager:
    def __init__(self):
        self.events = []

    def add_event(self, name, description, date, capacity):
        self.events.append(Event(name, description, date, capacity))

    def delete_event(self, name):
        self.events = [e for e in self.events if e.name != name]

    def register_participant(self, event_name, participant):
        for event in self.events:
            if event.name == event_name:
                for p in event.participants:
                    if participant.roll_number == p.roll_number:
                        return "Already registered!!"
            
                if len(event.participants) < event.capacity:
                    event.participants.append(participant)
                    participant.events.append(event_name)
                    return True
                else:
                    return False
        return None

    def search_participants(self, event_name):
        for event in self.events:
            if event.name == event_name:
                return [{"name": p.name, "roll": p.roll_number, "dept": p.department} for p in event.participants]
        return None
    
    def update_event(self, name, new_description=None, new_date=None, new_capacity=None):
        for event in self.events:
            if event.name == name:
                if new_description:
                    event.description = new_description
                if new_date:
                    event.date = new_date
                if new_capacity is not None:
                    event.capacity = int(new_capacity)
                return True
        return False


# Create Event Manager
manager = EventManager()

# HTTP Handler
class MyHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path=="/events":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            events_list = [
                    {
                        "name": e.name,
                        "desc": e.description,
                        "date": e.date,
                        "capacity": e.capacity,
                        "count": len(e.participants)
                    } for e in manager.events
            ]
            # self._send_json({"events": events_list})
            self.wfile.write(json.dumps({"events": events_list}).encode())

        else:
            super().do_GET()

    def do_POST(self):
        length = int(self.headers["Content-Length"])
        data = self.rfile.read(length)
        payload = json.loads(data.decode())

        if self.path == "/add_event":
            manager.add_event(payload["name"], payload["desc"], payload["date"], int(payload["capacity"]))
            self._send_json({"status": "success"})

        elif self.path == "/delete_event":
            manager.delete_event(payload["name"])
            self._send_json({"status": "deleted"})

        elif self.path == "/register":
            participant = Participant(payload["name"], payload["roll"], payload["dept"])
            result = manager.register_participant(payload["event"], participant)
            if result is True:
                self._send_json({"status": "registered"})
            elif result is False:
                self._send_json({"status": "full"})
            elif result == "Already registered!!":
                self._send_json({"status": "already_registered"})
            else:
                self._send_json({"status": "event_not_found"})


        elif self.path == "/search":
            participants = manager.search_participants(payload["event"])
            if participants is not None:
                self._send_json({"status": "found", "participants": participants})
            else:
                self._send_json({"status": "event_not_found"})
        
        elif self.path == "/update_event":
            updated = manager.update_event(
                payload["name"],
                payload.get("desc"),
                payload.get("date"),
                payload.get("capacity")
            )
            if updated:
                self._send_json({"status": "updated"})
            else:
                self._send_json({"status": "event_not_found"})


    def _send_json(self, data):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

# Run Server
PORT = 8000
with socketserver.TCPServer(("", PORT), MyHandler) as httpd:
    print(f"Server running at http://localhost:{PORT}")
    httpd.serve_forever()
