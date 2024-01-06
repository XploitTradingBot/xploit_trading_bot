import logging

adapter = logging.Logger(__name__)

# Creating handlers
c_handler = logging.StreamHandler()  # console handler
f_handler = logging.FileHandler('./file.log', mode="a")  # file handler
c_handler.setLevel(logging.INFO)
f_handler.setLevel(logging.WARN)

# Creating formats
c_format = logging.Formatter('%(asctime)s - %(message)s\n')
f_format = logging.Formatter(
    '%(asctime)s - %(levelname)s - %(message)s')
c_handler.setFormatter(c_format)
f_handler.setFormatter(f_format)


# Add handlers to the logger
adapter.addHandler(c_handler)
adapter.addHandler(f_handler)