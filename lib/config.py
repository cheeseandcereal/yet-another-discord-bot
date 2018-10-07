import configparser

config = configparser.ConfigParser()
config.readfp(open('config/config.ini'))


def get_config(key, section='settings'):
    return config.get(section, key)
