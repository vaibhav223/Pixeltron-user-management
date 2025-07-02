from datetime import datetime
import pytz

def convert_utc_to_timezone(utc_time_str: str, target_timezone_str: str) -> str:
    """
    Converts a UTC datetime string to a specified timezone.

    :param utc_time_str: UTC time in ISO 8601 format (e.g., "2025-06-09T13:30:00")
    :param target_timezone_str: Timezone string like 'Asia/Kolkata', 'America/New_York'
    :return: Converted time as a formatted string
    """
    # Parse input time assuming it's in UTC
    utc_time = datetime.fromisoformat(utc_time_str)
    utc_time = utc_time.replace(tzinfo=pytz.utc)

    # Convert to target timezone
    target_timezone = pytz.timezone(target_timezone_str)
    target_time = utc_time.astimezone(target_timezone)

    # Return formatted string
    return target_time.strftime('%Y-%m-%d %H:%M:%S %Z%z')

# Example usage
utc_input = "2025-06-14T15:00:00.000Z"
timezone = "Asia/Jakarta"
converted_time = convert_utc_to_timezone(utc_input, timezone)

print(f"UTC Time: {utc_input}")
print(f"Converted Time ({timezone}): {converted_time}")
