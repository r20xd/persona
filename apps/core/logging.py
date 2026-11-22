import logging


class SafeFormatter(logging.Formatter):
    """Discard arbitrary Django/third-party messages and exception payloads."""

    def format(self, record):
        if record.name == "deanery.http":
            message = record.getMessage()
        else:
            error_type = record.exc_info[0].__name__ if record.exc_info else "none"
            message = f"event=framework_error error_type={error_type}"
        return f"{record.levelname} {record.name} {message}"
