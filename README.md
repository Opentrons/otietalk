# Otietalk

> A collection of tools for interaction with the robot through the http API

## Install

### Dev container

- Have Docker installed.
- Clone the repo.
  - `git clone https://github.com/Opentrons/otietalk.git`
- Have VSCode open the dev container.
- Open VSCode command palette `command shift p`
- Select Python Interpreter ![Select the python interpreter](img/PythonSelectInterpreter.png)
  -  Select the .venv in this directory. ![Select the .venv in this directory](img/venv.png)
- Use the VSCode terminal not an external one.

## Heater Shaker commands

> From a terminal in the root directory of the repository

- Run
  - `pipenv run python hs_commands.py`
- Follow the prompts
- logs are in `responses.log`

## Heater Shaker Labware

> From a terminal in the root directory of the repository

- Run the wizard
  - `pipenv run python hs_labware.py`
- Follow the prompts

### Pretty print into a log file

go into the file `rich_it.py`
paste in your string to format in the variable `your_garbage`

```shell
pipenv run python rich_it.py
```

look in pretty.log for the output

### Other notes

> How to use pipenv to install direct `pipenv install -e git+https://github.com/kraanzu/textual_extras.git@main#egg=textual_extras`
