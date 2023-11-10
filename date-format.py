


def format_date(date):
    import datetime
    from datetime import timedelta
    """Formats a date to a relative time string, such as "1 min ago" or "1 hour ago".
    
    Args:
        date: A datetime object.

    Returns:
        A string representing the relative time between the given date and the current time.
    """

    now = datetime.datetime.now()
    delta = now - date

    if delta.seconds < 60:
        return f"{delta.seconds} seconds ago"
    elif delta.seconds < 3600:
        minutes = delta.seconds // 60
        return f"{minutes} minutes ago"
    elif delta.seconds < 86400:
        hours = delta.seconds // 3600
        return f"{hours} hours ago"
    else:
        days = delta.seconds // 86400
        return f"{days} days ago"

# Example usage:

date = datetime.datetime(2023, 11, 10, 3, 14, 39)
formatted_date = format_date(date)

print(formatted_date)