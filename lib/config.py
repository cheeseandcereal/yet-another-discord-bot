import configparser

config = configparser.ConfigParser()
config.readfp(open('config/config.ini'))


def get_config(key: str, section: str = 'settings'):
    """
    Get the config value for a certain setting

    Args:
        key: settings key to fetch
        section: section to retrieve the setting from
    Returns:
        string of fetched setting
    """
    return config.get(section, key)
