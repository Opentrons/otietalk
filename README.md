# Otietalk

> A collection of tools for interaction with the robot through the http API

## Install

> From a terminal

- Have a python 3.10.X installed
  - `python --version`
- Have pipenv installed
  - `pip install -U pipenv`
- clone the repo
  - `git clone https://github.com/Opentrons/otietalk.git`
- move into the repo you just cloned
  - `cd otietalk`
- Install the dependencies
  - `pipenv install`

## Heater Shaker commands

> From a terminal in the root directory of the repository

- Run
  - `pipenv python run hs_commands.py`
- Follow the prompts
- logs are in `responses.log`

## Heater Shaker Labware

> From a terminal in the root directory of the repository

- Run the wizard
  - `pipenv python run hs_labware.py`
- Follow the prompts

### Other notes

> How to use pipenv to install direct `pipenv install -e git+https://github.com/kraanzu/textual_extras.git@main#egg=textual_extras`
