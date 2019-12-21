# IISc-UG-Discord-Bot
A (discord.py) bot for the IISc UG Discord Server

This code is probably of no use to anyone else, but feel free to use it if you have a similar use case. 
 
All it does are provide you with a basic registration system based on an existing list of names of everyone that should be permitted to join the list. (along with the ability to register others with a different role), and possibly some basic moderation commands. WIP.
If you make any improvements, I'd love it if you'd make a pull request. Please read the [code of conduct](https://github.com/Lord-of-the-Galaxy/IISc-UG-Discord-Bot/blob/master/CODE_OF_CONDUCT.md) before making any contributions.

## How to run
You'll need Python 3 (it's been tested only with 3.7 though), along with all the libraries listed in `requirements.txt`.
First you need to create a `config.py` file. You just have to fill in everything in `config - Template.py` for this.
Secondly you'll also need a list of names (of those who should be allowed to join the server). Make sure to set it's path in `config.py`. An example would be:
```
FOO
BAR
FOOBAR
```
With this done, you can run the program with `python index.py`. By default it logs every message to both the log files and the terminal. To change this, you can modify the `log_level` and `output_level` to different things (they don't need to be the same ofc):
```
NONE    : No messages
ERROR   : Only errors
WARN    : Warnings and higher
SUCCESS : Success messages and higher
INFO    : Information messages and higher
DEBUG   : All messages
```

## How to use
Just run the `help` command (as moderator, in the welcome channel) once the bot is up and running (default prefix is `!`)

## Bugs etc
Feel free to [file an issue](https://github.com/Lord-of-the-Galaxy/IISc-UG-Discord-Bot/issues/new), or better yet, open a pull request if you manage to fix the bugs.
If you need some help with this/have some feedback, you can file an issue anyways, and I'll look into it. Preferably tag the issue appropriately.
