import logging
import inspect

def get_calling_module_name():
    """
    gets the name of the module that calls this function.

    This function uses the 'inspect' module to get information about the
    current frame and its caller. It then extracts the '__name__' attribute
    from the caller's global dictionary, which represents the module name.
    """
    # Get the current frame
    current_frame = inspect.currentframe()

    # Get the frame of the caller (the module that imported and called this function)
    caller_frame = current_frame.f_back

    # Access the global dictionary of the caller's frame
    # The '__name__' key in this dictionary holds the module's name
    if caller_frame:
        return caller_frame.f_globals.get('__name__')
        


def get_logger(name:str=None, level=logging.INFO):
    """
    Creates and returns a logger instance.

    Args:
        level (int): The logging level (e.g., logging.INFO, logging.DEBUG).

    Returns:
        logging.Logger: Configured logger instance.
    """
    logger = logging.getLogger(__name__)
    logger.setLevel(level)

    # Clear existing handlers to prevent duplicate logs
    if not logger.hasHandlers():
        stream_handler = logging.StreamHandler()
        stream_handler.setLevel(level)
        logger_prefix = f"{name} - {level}"
        stream_handler.setFormatter(logging.Formatter(f'%(asctime)s - {logger_prefix} - %(message)s'))
        logger.addHandler(stream_handler)

    return logger