from datetime import datetime


# This is a substitute for what a JWT token would really be
def get_datetime():
    print(f"Current datetime: {datetime.now()}")
