# requirements/

Plain-pip mirror of `pyproject.toml`, for environments without uv or poetry.

| file       | contents                                  |
|------------|-------------------------------------------|
| `base.txt` | runtime only                              |
| `prod.txt` | `base` + the release extras               |
| `test.txt` | `base` + the test group                   |
| `dev.txt`  | `test` + the dev group                    |

```bash
pip install -r requirements/dev.txt     # local
pip install -r requirements/prod.txt    # container
```

Three toolchains describe the same set — when you add a dependency, add it to
`[project.dependencies]`, the matching `[tool.poetry.group.*]`, and the right
file here.
