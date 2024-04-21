Pythomat
========

Pythomat is the ideal helper for (lazy) students. Anyone familiar with the flood of script versions, exercise sheets and lecture recordings knows how annoying it can be to keep your digital copy of them up to date so that you can access them on the bus, train or in Saarland without having to deal with slow mobile connections. As apparently making the files available as a shared folder in the [Nextcloud instance of the subject area](https://oc.cs.uni-saarland.de/) requires too much computer magic, Pythomat helps you automate downloading scripts.

Pythomat is easy to extend, small and (relatively) quick to install. It is written in Python because *Cehmat*, *Javamat*, *Essemelmat* or *OCamlmat* just sounds bonkers. And because Python is platform-independent. And, because the (original) author didn't know it when he started the script.

# Prerequisites
Python 3, as well as the package Mechanize, and when using the module [*cms*](#cms-1) or [*moodle*](#moodle-1) BeautifulSoup4 and Keyring, are required.

# Installation
- Install [Python 3](https://python.org/).
- Install [pip](https://pip.pypa.io/en/stable/installing/). This is for easy installation of the dependencies.
- Run `git clone https://github.com/muekoeff/pythomat.git && cd pythomat`; or [download](https://github.com/muekoeff/pythomat/archive/master.zip) this repo and unpack it into a directory.
- To ignore server-side changes to `pythomat.ini`, it is recommended to have Git ignore this file. This is possible, for example, by executing the command `echo "pythomat.ini" >> "$(git rev-parse --show-toplevel)/.git/info/exclude"` in the local Git repository directory.
- If the [*youtube*](#youtube) mode is used:
  - Install [*youtube-dl*](https://ytdl-org.github.io/youtube-dl/) via your system's package manager.
  - Or download *youtube-dl*, then move the downloaded file to the created directory.

## Manual Installation
When using `pythomat.sh`, you don't have to take care of installation of dependencies. If you want to do that manually:

- Create a virtual environment by running `python -m venv venv`.
- Load the virtual environment by running `source venv/bin/activate`.
- Either…
  - Install all required dependencies with `pip3 install .`.
  - Install dependencies manually:
    - Run `pip3 install mechanize`.
    - If modules [*cms*](#cms-1) or [*moodle*](#moodle-1) are used:
      - Run `pip3 install beautifulsoup4 keyring --upgrade keyrings.alt`.

## Updating
Git can be used for updating Pythomat. There is no automated mechanism for updating or checking for updates. If required, the project can be subscribed to on GitHub so that you receive notified via email.
- Change to the Pythomat directory.
- Ensure that `pythomat.ini` is excluded from updates using `echo "pythomat.ini" >> "$(git rev-parse --show-toplevel)/.git/info/exclude"` (not necessary if it is unchanged).
- `git pull`

# Running
- Run `pythomat.sh`¹.
- Optionally, an alternative \*.ini file can be passed as an argument. By default, `pythomat.ini` is read in the working directory.

Personally, I have created a desktop shortcut with the following command so that the output remains open even after completion:

```shell
/usr/bin/env sh -c '"/path/to/pythomat.sh" --log "/path/to/Pythomat.log" "/path/to/Pythomat.ini"; echo "Press Any Key To Exit…" && read name'
```

¹ `pythomat.sh` is a wrapper for `pythomat.py` that takes care of setting up or loading a virtual environment.

## Arguments
| Parameter       | Description |
| --------------- | ----------- |
| `--createdirs`  | Automatically create missing directories to download to. |
| `-h`, `--help`  | Display a list of all supported arguments. |
| `-l`, `--list`  | Display a list of all rules specified in the `pythomat.ini`. |
| `--log <path>`  | Log downloaded files to the specified path. |
| `-r`, `--rules` | Only execute the rules separated by commas. Rules not listed are omitted. With the value `all`, all rules are executed, even those that are normally omitted with `skip`. |
| `--version`     | Display a link to the GitHub repository. |

# Configuration
Pythomat uses the standard ConfigParser library to parse ini files. By default, `pythomat.ini`in the current working directory is used.

Here is an example file that downloads a single script. The name of the section, specified in a separate line in square brackets, can be chosen freely:

```ini
[LectureScript]
mode = single
uri = https://some.chair.uni-saarland.de/script.pdf
saveto = /some/path/
```

## Modes
The parameter `mode` determines which of the available modes to use: [`batch`](#batch), [`cms`](#cms), [`module`](#module), [`moodle`](#moodle), [`single`](#single), [`youtube`](#youtube)

### `batch`
Search a page for links and download all matched files.

#### Parameters
| Parameter           | Description |
| ------------------- | ----------- |
| `uri`               | URL to search for links. |
| `saveto`            | Directory to which the files are to be downloaded. |
| `detect`            | Directory to be searched for whether a filename already exists and therefore whether the file has already been downloaded. Corresponds to `saveto` if not specified. |
| `detect_recursive`  | Whether the `detect` directory should be searched recursively. |
| `pattern`           | Regular expression that the link must fulfil in order to be downloaded. |
| `username`          | *optional:* Username for HTTP authentication. Only to be used together with `password`. |
| `password`          | *optional:* Password for HTTP authentication. Only to be used together with `username`. |
| `overwrite`         | *optional:* Whether an existing file at the same path may be overwritten. `1` corresponds to yes, `0` corresponds to no. If not specified, `1`. |
| `skip`              | *optional:* If set to `1`, this rule is only executed if it is listed in the `--rules` argument. |

### `cms`
Short form for a module call with *cms* as module. See [the corresponding section](#cms-1).

### `moodle`
Short form for a module call with *moodle* as module. See [the corresponding section](#moodle-1).

### `module`
Load `<module>.py` and execute `<module>.start(section, items, pythomat)`.
`section` is the name of the current configuration as a string, `items` is a dictionary containing the settings, and `pythomat` is a reference to the `pythomat` object.
The `pythomat` reference should be used to call `reportFailed(section, filename)` and `reportFinished(section, filename)` in order to be listed in the final report. ([Listing of modules](#module-1))

#### Parameters
| Parameter             | Description |
| --------------------- | ----------- |
| `module`              | Name of the module to be loaded. (corresponds to filenames without `.py` file extension) |
| `skip`                | *optional:* If set to `1`, this rule is only executed if it is listed in the `--rules` argument. |
| *dependent on module* | Modules can introduce further parameters. |

### `single`
Download a single file if it has been changed on the server.

| Parameter           | Description |
| ------------------- | ----------- |
| `uri`               | URL of the file to download. |
| `saveto`            | Directory to which the file is to be downloaded. |
| `detect`            | Directory to be searched to see whether a filename already exists and therefore whether the file has already been downloaded. Corresponds to `saveto` if not specified. |
| `detect_recursive`  | Whether the `detect` directory should be searched recursively. |
| `filename`          | *optional:* Filename for the downloaded file. If not specified, the filename is taken from `uri`. |
| `username`          | *optional:* Username for HTTP authentication. Only to be used together with `password`. |
| `password`          | *optional:* Password for HTTP authentication. Only to be used together with `username`. |
| `overwrite`         | *optional:* Whether an existing file at the same path may be overwritten. `1` corresponds to yes, `0` corresponds to no. If not specified, `1`. |
| `skip`              | *optional:* If set to `1`, this rule is only executed if it is listed in the `--rules` argument. |

### `youtube`
**Legacy.** Downloads a single YouTube video of the given id.

| Parameter   | Description |
| ----------- | ----------- |
| `uri`       | |
| `saveto`    | |
| `overwrite` | *optional:* Whether an existing file at the same path may be overwritten. `1` corresponds to yes, `0` corresponds to no. If not specified, `1`. |

## Module
Modules are used with the mode `mode = module`. To do this, the name of the mode to be loaded must be entered in `module`. Additional modules are easy to create. The following modules are available: [`cms`](#cms-1), [`moodle`](#moodle-1).

### `cms`
Support for CakeCMS material pages.

| Parameter           | Description |
| ------------------- |-------------|
| `uri`               | URL of the main page of the CMS. |
| `saveto`            | Directory to which the files are to be downloaded. |
| `detect`            | Directory to be searched to see whether a filename already exists and therefore whether the file has already been downloaded. Corresponds to `saveto` if not specified. |
| `detect_recursive`  | Whether the `detect` directory should be searched recursively. |
| `username`          | Username in the CMS instance. |
| `password`          | *instead of `keyring_id`* <br> Password corresponding to the `username` in cleartext. |
| `keyring_id`        | *instead of `password`* <br> Identifier, which is assembled to the service `pythomat.<keyring_id>`. If there is no password in the system keyring under the identifier, the user is prompted to enter one. This is saved in the keyring. |
| `fileext_whitelist` | *optional:* Space-separated list of file extensions that are to be downloaded. |
| `fileext_blacklist` | *optional:* Space-separated list of file extensions that should not be downloaded. |
| `overwrite`         | *optional:* Whether an existing file at the same path may be overwritten. `1` corresponds to yes, `0` corresponds to no. If not specified, `0`. |

### `moodle`
Support for Moodle instances.

| Parameter           | Description |
| ------------------- | ----------- |
| `uri`               | URL of the main page of the event on Moodle. |
| `saveto`            | Directory to which the files are to be downloaded. |
| `detect`            | Directory to be searched to see whether a filename already exists and therefore whether the file has already been downloaded. Corresponds to `saveto` if not specified. |
| `detect_recursive`  | Whether the `detect` directory should be searched recursively. |
| `username`          | Benutzername in der Moodle-Instanz. |
| `password`          | *instead of `keyring_id`* <br> Password corresponding to the `username` in cleartext. |
| `keyring_id`        | *instead of `password`* <br> Identifier, which is assembled to the service `pythomat.<keyring_id>`. If there is no password in the system keyring under the identifier, the user is prompted to enter one. This is saved in the keyring. |
| `fileext_whitelist` | Space-separated list of file extensions that are to be downloaded. |
| `overwrite`         | *optional:* Whether an existing file at the same path may be overwritten. `1` corresponds to yes, `0` corresponds to no. If not specified, `0`. |
