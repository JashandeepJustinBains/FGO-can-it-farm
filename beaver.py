import logging

class Beaver:

    def __init__(self, name):
        global logger1
        global logger2
        # Configure the first logger for the log file
        logger1 = logging.getLogger(f'logger1_{name}')
        logger1.setLevel(logging.DEBUG)
        file_handler1 = logging.FileHandler(f'log_file_{name}.log')
        formatter1 = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler1.setFormatter(formatter1)
        logger1.addHandler(file_handler1)

        # Configure the second logger for the other file
        logger2 = logging.getLogger(f'logger2_{name}')
        logger2.setLevel(logging.DEBUG)
        file_handler2 = logging.FileHandler(f'output_file_{name}.log')
        formatter2 = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler2.setFormatter(formatter2)
        logger2.addHandler(file_handler2)

        # Log messages to the first file
        logger1.debug('This is a debug message for the log file.')
        logger1.info('This is an info message for the log file.')
        logger1.warning('This is a warning message for the log file.')

        # Log messages to the second file
        logger2.debug('This is a debug message for the other file.')
        logger2.info('This is an info message for the other file.')
        logger2.warning('This is a warning message for the other file.')

        # return logger1, logger2



# Instantiate the Beaver class to initialize the loggers
# beaver_instance = Beaver()

# Ensure logger1 and logger2 are defined at the module level
# logger1 = logging.getLogger('logger1')
# logger2 = logging.getLogger('logger2')