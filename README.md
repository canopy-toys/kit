# kit

Everything that makes the canopy toy repositories: a template for each, the issue catalog, the bot's workflow, and
the script that sets them up and resets them. The plan is `docs/TOY_REPOS.md` in
[canopy](https://github.com/eddieland/canopy).

- `templates/<repo>/`: a toy repository's first commit, tagged `seed`. `templates/common/` is laid over every one: CI,
  the outage switch, and `toy-bot.yml`.
- `issues/<repo>/NN-slug.md`: the catalog. Front matter: `title`, `scenario`, and optionally `autolabel: true` (the
  queue label at seed time) and `blocked_by: <slug>, ...`.
- `kit.toml`: the org and the labels.
- `toys.py`: `./toys.py setup <repo>`, then `./toys.py reset <repo|all>` to go back to the seed. It needs `uv` and an
  admin `gh` with the `repo` and `workflow` scopes.
