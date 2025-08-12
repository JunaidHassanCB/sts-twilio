import os
import requests

from constants.constants import BASE_URL, CONFIG


def get_api_key_cal() -> str:
    api_key = os.getenv("CAL_COM_API_KEY")
    if not api_key:
        raise ValueError("CAL_COM_API_KEY environment variable is not set")
    return api_key


def get_request_headers() -> dict:
    return {
        # "Authorization": f"Bearer {get_api_key_cal()}",
        "Content-Type": "application/json"
    }


def get_available_slots(event_type_id: int, start: str, end: str, time_zone: str) -> dict:
    url = f"{BASE_URL}/slots"
    headers = {
        **get_request_headers(),
        "cal-api-version": "2024-09-04",
    }
    params = {
        "eventTypeId": event_type_id,
        "start": start,
        "end": end,
        "timeZone": time_zone,
    }
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print("Error fetching slots:", e)
        raise


def reserve_slot(event_type_id: int, slot_start: str) -> dict:
    url = f"{BASE_URL}/slots/reservations"
    headers = {
        **get_request_headers(),
        "cal-api-version": "2024-09-04",
    }
    payload = {
        "eventTypeId": event_type_id,
        "slotStart": slot_start,
    }
    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print("Error reserving slot:", e)
        raise


def book_appointment(attendee: dict, event_type_id: int, start: str) -> dict:
    url = f"{BASE_URL}/bookings"
    headers = {
        **get_request_headers(),
        "cal-api-version": "2024-08-13",
    }
    payload = {
        "attendee": attendee,
        "eventTypeId": event_type_id,
        "start": start,
    }
    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print("Error booking appointment:", e)
        raise
