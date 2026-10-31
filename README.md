# Robot Agents in Production: teaching labs

[![Binder](https://binder.intel4coro.de/badge_logo.svg)](https://binder.intel4coro.de/v2/gh/beetz-m/robot-agents-production-labs/main?urlpath=lab/tree/notebooks/lab03_flow_laws.ipynb)

Notebook labs for the textbook *Robot Agents in Production: from competence to site output* (AICOR, in preparation).
They run on a small teaching model of production lines, docks, supply robots and a factory feeding a seasonal
installation campaign. The model is written for teaching: **every parameter is ILLUSTRATIVE** (`register.yaml`), it is
not calibrated to any plant, and it contains no data of any company.

This lab is part of the [EASE Virtual Research Building (VRB)](https://vrb.ease-crc.org/) family of Binder labs.

## Launch

| Interface | Link |
|-----------|------|
| JupyterLab (opens the first lab) | https://binder.intel4coro.de/v2/gh/beetz-m/robot-agents-production-labs/main?urlpath=lab/tree/notebooks/lab03_flow_laws.ipynb |
| VSCode | https://binder.intel4coro.de/v2/gh/beetz-m/robot-agents-production-labs/main?urlpath=vscode |

The first launch after a push builds the Docker image and can take a long time. Later launches reuse the image.
To freeze the lab to a specific version, replace `main` in the URL with a tag or a commit hash.

## Labs

| Notebook | Chapter | Question |
|---|---|---|
| `notebooks/lab03_flow_laws.ipynb` | 3 Flow laws | Does Little's law hold with measured work in process? What does each buffer place buy? |
| `notebooks/lab04_competence.ipynb` | 4 Competence as parameters | How much of the supply robots' gain survives imperfect robots, against their expected net relief? |
| `notebooks/lab05_staircase.ipynb` | 5 Where competence becomes output | Relief at one station, at the constraint, everywhere |
| `notebooks/lab06_pooling_docks.ipynb` | 6 Lines, docks, pooling | Fixed crews, floaters, specialist and cross-trained crews: which comparisons are fair? |
| `notebooks/lab07_breakdowns_rework.ipynb` | 7 Variants and breakdowns | Short against long repairs, line against docks; rework into the line against a bay |
| `notebooks/lab10_ranking.ipynb` | 10 Ranking over ranges | Where in a parameter box does the robot decision flip between a factory alone and one coupled to its campaign? |

Each notebook asks for a written prediction before anything runs and ends with questions.

## What is inside

- `tmodel/` – the teaching model: a small discrete-event kernel (`des.py`), a production line (`line.py`), robot
  competence profiles (`robots.py`), docks (`docks.py`), a seasonal chain as a linear program (`chain.py`)
- `labs/` – the lab scripts (source of truth); `tools/make_notebooks.py` builds `notebooks/` from them
- `tests/` – 16 checks against laws and closed forms (`python3 -m pytest tests -q`)
- `register.yaml` – every parameter with its provenance (all ILLUSTRATIVE)
- `binder/Dockerfile`, `binder/entrypoint.sh`, `requirements.txt` – how the image is built; `binder/docker-compose.yml`
  – run the lab locally

## Run locally

Without Docker: `pip install -r requirements.txt`, then `python3 -m pytest tests -q` and `cd labs && python3 lab03_flow_laws.py`.

With Docker and Docker Compose on Linux:

```bash
docker compose -f binder/docker-compose.yml up --build
# open http://localhost:8888
docker compose -f binder/docker-compose.yml down
```

## Credits

Created with the `setup-vrb-lab` skill from [aicor-vrb/binder-template](https://github.com/aicor-vrb/binder-template).
Licence: Apache 2.0 (`LICENSE`).
