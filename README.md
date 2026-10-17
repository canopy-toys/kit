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
  admin `gh` with the `repo` and `workflow` scopes, and the org's "Allow GitHub Actions to create and approve pull
  requests" turned on (Settings, Actions, General), which no repository setting can override.
- `config/` and `workspace/`: the toy config root and workspace map. `./toys.py install` copies them under
  `~/canopy-toys`, keeping any file already there. The toy token goes in `~/canopy-toys/config/opencode/github-token`,
  written by the operator; the kit never holds it.

Run canopy on the toys through a wrapper that sets the config root, `~/canopy-toys/toycanopy`:

```sh
#!/bin/sh
export XDG_CONFIG_HOME="$HOME/canopy-toys/config"
exec uv run -q --project "$HOME/workspace/eddieland/canopy" canopy "$@"
```

Then, from `~/canopy-toys/workspace`: `toycanopy workspace sync`, `toycanopy tick --dry-run`, `toycanopy tick`.
