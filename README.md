# reddit [/u/storytellingbot](http://www.reddit.com/u/storytellingbot)

Experimental interactive storytelling comment bot


## Authors

- Theo Pak [@theopak](http://github.com/theopak)
- Laura


## Getting Started

Use the `$ git clone --recursive` option to clone the submodules (ie, the git repos within this repo) when you want to get started.

If you want to post to http://reddit.com when running the bot then you must enter a username and password into the [localsettings.py](localsettings.py) file. **Do not commit your password** or else you will have to change it immediately because this repo is public.

```sh
# Download a copy of the project git repo for the first time
git clone --recursive https://github.com/theopak/storytellingbot.git
cd storytellingbot
```

Use these regex for data aquisition:

```regex
s/^[^"][^a-z]*$//g
s/\n\n/\n/g
```

## Open Source

Refer to [LICENSE](LICENSE).
