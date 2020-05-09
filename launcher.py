from configparser import ConfigParser
from songwriters import songwriter
import contextlib
import logging
import click

parser = ConfigParser()
parser.read('bot-config.ini')


@contextlib.contextmanager
def setup_logging():
    global logger
    try:
        # __enter__
        dt_fmt = '%Y-%m-%d %H:%M:%S'
        fmt = logging.Formatter('[{asctime}] [{levelname:<7}] {name}: {message}', dt_fmt, style='{')
        logging.getLogger("discord").setLevel(logging.INFO)
        logging.getLogger("discord.http").setLevel(logging.INFO)

        logger = logging.getLogger()
        logger.setLevel(logging.INFO)

        file_hdlr = logging.FileHandler(
            filename='logs/songwriters-main.log',
            encoding="utf-8",
            mode='a')
        file_hdlr.setFormatter(fmt)
        logger.addHandler(file_hdlr)

        stderr_hdlr = logging.StreamHandler()
        stderr_hdlr.setFormatter(fmt)
        stderr_hdlr.setLevel(logging.DEBUG)
        logger.addHandler(stderr_hdlr)

        yield
    finally:
        # __exit__
        handlers = logger.handlers[:]
        for hdlr in handlers:
            hdlr.close()
            logger.removeHandler(hdlr)


def run_bot():
    bot = songwriter()
    bot.run()


@click.group(invoke_without_command=True, options_metavar='[options]')
@click.pass_context
def main(ctx):
    if ctx.invoked_subcommand is None:
        with setup_logging():
            run_bot()


if __name__ == '__main__':
    main()
