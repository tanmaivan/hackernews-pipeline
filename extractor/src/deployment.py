from prefect.schedules import Interval
from .hn_extractor_flow import hn_extractor_flow
from datetime import timedelta, datetime

hn_extractor_flow.serve(
    name="hn-extractor-deploy",
    schedule=Interval(
        timedelta(minutes=30),
        anchor_date=datetime(2025, 1, 1, 0, 0, 0),
        timezone="UTC",
    ),
)
