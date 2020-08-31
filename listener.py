import datetime
import logging
from logging import handlers


def listener_configurer():
    root = logging.getLogger()
    now = datetime.datetime.now()
    dtime = (now.year, 
             str(now.month).zfill(2), 
             str(now.day).zfill(2),
             str(now.hour).zfill(2),
             str(now.minute).zfill(2),
             str(now.second).zfill(2))
    log_file = 'QChecker_{}{}{}_{}{}{}.log'.format(*dtime)
    file_handler = handlers.RotatingFileHandler(log_file, 'a')
    console_handler = logging.StreamHandler()
    format = '%(asctime)s [%(module)-10s:%(lineno)-4d] %(levelname)s %(message)s'
    formatter = logging.Formatter(format, "%Y-%m-%d %H:%M:%S")
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    root.addHandler(file_handler)
    root.addHandler(console_handler)
    root.setLevel(logging.INFO)


def listener_process(queue):
    listener_configurer()
    while True:
        while not queue.empty():
            record = queue.get()
            logger = logging.getLogger(record.name)
            logger.handle(record)
