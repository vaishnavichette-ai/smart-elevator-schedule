# LiftLab — Smart Elevator Scheduler

LiftLab is a Flask prototype that compares two ways to schedule one elevator's pickup calls: nearest-call greedy and a priority queue. Configure the building, starting floor, travel and boarding time, and each request's floor, release time, and priority. The interface shows the selected pickup order, arrival and wait times, average and maximum wait, and travel time for both strategies.

## Run locally

1. Install Python 3.
2. Install Flask:
   `python -m pip install -r requirements.txt`
3. Start the app:
   `python app.py`
4. Open http://127.0.0.1:5000 in your browser.

Keep `app.py` and `index.html` in the same folder. The Flask server serves the HTML page and its scheduling API.

## Algorithms

- **Nearest-call greedy:** choose the closest currently available pickup; break ties by release time, then call ID.
- **Priority queue:** select the highest-priority available call (5 is most urgent); break ties by earlier release, current distance, then call ID. The heap is rebuilt each decision so the distance tie-break reflects the elevator's current floor.

## Scope

This is a deterministic educational simulator for one elevator and pickup calls. It does not model passenger destinations, multiple elevators, or live building controls. Results illustrate trade-offs for the chosen input set and are not a general performance guarantee.
