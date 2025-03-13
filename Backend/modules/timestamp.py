from datetime import datetime as Datetime

def generate_timestamp(datetime: Datetime | None = None) -> int:
    """
    Generate timestamp. If datetime param is not provided, current datetime will be used.
    """
    if datetime is None:
        return int(Datetime.now().timestamp())
    return int(datetime.timestamp())


def read_timestamp(timestamp: int) -> Datetime:
    """ Read POSIX timestamp. """
    return Datetime.fromtimestamp(timestamp)


def convert_to_readable(timestamp: int) -> str:
    """ Convert timestamp into string with date and time in readable form. """
    dt = read_timestamp(timestamp)
    return f"{dt.day:02d}/{dt.month:02d}/{dt.year} {dt.hour:02d}:{dt.minute:02d}"


def timestamp_to_page_displayable(timestamp: int) -> str:
    """ Convert timestamp into strig with format: DD/MM/YYYY """
    dt = read_timestamp(timestamp)
    return f"{dt.day:02d}/{dt.month:02d}/{dt.year}"


def convert_to_timestamp(readable: str) -> int:
    """ Convert date in format made by convert_to_readable() back to timestamp. """
    date_format = "%d/%m/%Y %H:%M"
    parsed_datetime = Datetime.strptime(readable, date_format)
    posix_timestamp = parsed_datetime.timestamp()
    return int(posix_timestamp)


def get_readable_time() -> str:
    """ Get current time and format it into: 31/12/2000 18:30:20 """
    return Datetime.now().strftime("%d/%m/%Y %H:%M:%S")


def get_date_file_format() -> str:
    """ Get current date and format it into: 2000_12_31 """
    return Datetime.now().strftime("%Y_%m_%d")
