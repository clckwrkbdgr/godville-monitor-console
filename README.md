PyGod
=====

Console monitor for ZPG "God watching over hero"-like games (Godville, The Tale etc) written on Python with curses library usage.

Currently supports following ZPG games:

- [Godville](godville.net) (AKA Russian Godville)
- [Godville Game](godvillegame.com) (AKA English Godville)
- [The Tale](the-tale.org)

Features
--------

- Minimalistic design
- Hero status parsing and pop-up windows for the following situations
	- hero's health is low
	- there is an inventory item that can be activated
	- session is expired
	- or any other user-defined states.


Requirements
------------

1. Linux/Unix/MacOS
2. Python3 installed


Usage
-----

Regular usage:

`$python3 pygod.py god_name`

If you want more information about usage:

`$python3 pygod.py -h`



Support
-------

In case of any issues with this program please create an issue on GitHub, or
describe it at [forum](https://godville.net/forums/show_topic/3148).

Also, it is recommended to attach the `pygod.log` file, automatically written
in application root directory, and run the application in DEBUG mode in order
to provide more informative log file:

`python3 pygod.py god_name -D`

Translation
-----------

Translation is done using `gettext`. Compiled translation files are located in `~/.local/share/pygod/<lang>/LC_MESSAGES/pygod.mo`.
To translate to a new language use following instructions (example for Ukrainian language, `uk_UA`):

	# Create template file messages.pot:
	find . -name '*py' | xargs pygettext -k tr
	# Create custom translation file for specific locale:
	msginit -i messages.pot -o share/uk/LC_MESSAGES/pygod.po -l uk_UA
	# Translate strings in created file using your favorite editor.
	# Make sure that encoding in metainfo matches encoding of the file itself.
	# Compile translation file:
	msgfmt -o ~/.local/share/pygod/uk/LC_MESSAGES/pygod.mo share/uk/LC_MESSAGES/pygod.po
