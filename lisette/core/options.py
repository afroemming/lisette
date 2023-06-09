import lisette.lib.config as config
import lisette.lib.logging as logging

lis_options = [
    config.Option(
        "log_level",
        arguments={
            "help": "Level messages to log.",
            "choices": ("DEBUG", "INFO", "WARNING", "CRITICAL"),
        },
        post_load=logging.get_numeric,
    ),
    config.Option(
        "token", arguments={"help": "Discord bot token to use."}, required=True
    ),
    config.Option(
        "db_path", arguments={"help": "Path to sqlite db file."}, required=True
    ),
    config.Option(
        "env_file", arguments={"help": "Path to env file to load enviroment from"}
    ),
]
