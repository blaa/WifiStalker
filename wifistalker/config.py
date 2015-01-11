"""
Default configuration
"""

version="v0.0.1"

# Default connection parameters - overwriten by command parameters
db = {
    'name': 'wifistalker',
    # Localhost
    'conn': None,
}


hopper = {
    'max_karma': 10,
}

# For Frames class
beacon_filter = {
    'enabled': True,

    # Run cleanup process on cache every x seconds
    'cleanup_interval': 10 * 60,
    # include a packet if an averaged strength deviates by more than X from last stored frame
    'max_str_dev': 10,
    # Include at least one per X seconds
    'max_time_between': 5 * 60,
}
