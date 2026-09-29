"""Resolved paths for the build pipeline, loaded from site.config.json.

The "base path" is the support-folder root: by default the parent of this
scripts/ directory, overridable with the FRAGILEPEACE_SUPPORT_DIR environment
variable. Every path in site.config.json is resolved relative to that base, so
nothing is hardcoded and the same scripts work for any support folder that
carries its own site.config.json.

Mirrors the contract in Caul's caul-support/scripts/config.py.

Usage:
    from config import cfg
    cfg.ROOT, cfg.SRC, cfg.CHRONICLE, ...
"""
import json
import os

_HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.abspath(os.environ.get("FRAGILEPEACE_SUPPORT_DIR", os.path.join(_HERE, "..")))
_CONFIG_PATH = os.path.join(BASE, "site.config.json")


class _Config:
    def __init__(self, base, data):
        self.BASE = base
        self.TITLE = data["title"]

        def rel(p):
            return os.path.join(base, p)

        # the site repo, a sibling of this support folder
        self.ROOT = os.path.abspath(os.path.join(base, data["output_repo"]))

        def in_repo(p):
            return os.path.join(self.ROOT, p)

        src = data["sources"]
        self.SRC = rel(src["obsidian"])          # the Archivist export
        self.FOUNDRY_DIR = rel(src["foundry"])   # Foundry actor exports

        # Where the generated pages live. The repo root before the VTT fork; campaign/
        # after it, because the VTT owns the root (campaign/PLAN.md M1).
        self.SITE = os.path.abspath(os.path.join(self.ROOT, data.get("site_root", "")))

        ri = data["repo_inputs"]
        self.CHRONICLE = in_repo(ri["chronicle"])
        self.ENTITIES = in_repo(ri["entities"])
        # repo-relative forms, for tools that address them through git
        self.CHRONICLE_REL = ri["chronicle"]
        self.ENTITIES_REL = ri["entities"]
        self.ACCEPT = in_repo(ri["accept_table"])

        self.DOJI_SETSUNA = rel(data["tools"]["doji_setsuna"])

        # the l5r5e rules corpus the sheet builders read verbatim rules text from
        self.DSL_L5R5E = os.path.expanduser(data["external"]["dsl_l5r5e"])


with open(_CONFIG_PATH, encoding="utf-8") as _f:
    cfg = _Config(BASE, json.load(_f))
