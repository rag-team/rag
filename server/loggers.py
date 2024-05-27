import logging


def splitOutErrLogger(
    out, err, name=None, format=logging.BASIC_FORMAT, level=logging.DEBUG
):
    name = name or __name__

    log = logging.getLogger(name)
    log.setLevel(level)

    # Create formatter
    formatter = logging.Formatter(format)

    # Stream handler
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(level)
    stream_handler.setFormatter(formatter)

    # File handler for output log
    file_handler_out = logging.FileHandler(out)
    file_handler_out.setLevel(logging.DEBUG)
    file_handler_out.setFormatter(formatter)

    # File handler for error log
    file_handler_err = logging.FileHandler(err)
    file_handler_err.setLevel(logging.ERROR)
    file_handler_err.setFormatter(formatter)

    # Add handlers to the logger
    log.addHandler(stream_handler)
    log.addHandler(file_handler_out)
    log.addHandler(file_handler_err)

    return log


def fileLogger(filename, name=None, format=logging.BASIC_FORMAT, level=logging.DEBUG):
    name = name or __name__

    log = logging.getLogger(name)
    log.setLevel(level)

    # Create formatter
    formatter = logging.Formatter(format)

    # File handler
    file_handler = logging.FileHandler(filename)
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)

    # Add handlers to the logger
    log.addHandler(file_handler)

    return log
