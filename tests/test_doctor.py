"""Tests for setup.py --check / --fix (the doctor).

    python3 -m unittest discover -s tests -v

Only the pure drift logic is tested here: it turns brew's JSON and a few file
contents into findings. The brew/nvm/rbenv calls around it are thin wrappers.
"""
import builtins
import importlib.util
import os
import unittest
from unittest import mock

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load_setup():
    """Import setup.py without running the interactive setup."""
    spec = importlib.util.spec_from_file_location("mac_setup", os.path.join(ROOT, "setup.py"))
    module = importlib.util.module_from_spec(spec)
    with mock.patch.object(builtins, "input", side_effect=AssertionError("setup prompted on import")):
        spec.loader.exec_module(module)
    return module


setup = load_setup()


def formula(name, aliases=(), oldnames=(), deprecated=False, disabled=False, reason=None):
    return {
        "name": name, "aliases": list(aliases), "oldnames": list(oldnames),
        "deprecated": deprecated, "disabled": disabled,
        "deprecation_reason": reason if deprecated else None,
        "disable_reason": reason if disabled else None,
    }


def cask(token, old_tokens=(), deprecated=False, disabled=False, reason=None):
    return {
        "token": token, "old_tokens": list(old_tokens),
        "deprecated": deprecated, "disabled": disabled,
        "deprecation_reason": reason if deprecated else None,
        "disable_reason": reason if disabled else None,
    }


BREW = {
    "formulae": [
        formula("python@3.14", aliases=["python", "python3"]),
        formula("pkgconf", aliases=["pkg-config"]),
        formula("tldr", deprecated=True, disabled=True, reason="unmaintained"),
    ],
    "casks": [
        cask("docker-desktop", old_tokens=["docker"]),
        cask("quicklook-csv", disabled=True, reason="no_longer_meets_criteria"),
        cask("macdown", disabled=True, reason="fails_gatekeeper_check"),
    ],
}


def findings_for(expected_formulae=(), expected_casks=(), replaced=None, brew=BREW):
    index = setup.installed_index(brew)
    return setup.package_findings(
        set(expected_formulae), set(expected_casks),
        replaced if replaced is not None else setup.REPLACED, index,
    )


def subjects(findings, kind):
    return {f.subject for f in findings if f.kind == kind}


class ImportTest(unittest.TestCase):
    def test_import_does_not_run_setup(self):
        self.assertTrue(callable(setup.main))


class PackageListTest(unittest.TestCase):
    def test_replaced_packages_are_not_expected(self):
        expected = setup.expected_formulae() | setup.expected_casks()
        self.assertFalse(expected & set(setup.REPLACED))

    def test_every_replacement_is_expected(self):
        expected = setup.expected_formulae() | setup.expected_casks()
        targets = {new for new in setup.REPLACED.values() if new}
        self.assertEqual(targets - expected, set())


class PackageFindingsTest(unittest.TestCase):
    def test_alias_satisfies_expected_formula(self):
        self.assertEqual(subjects(findings_for(["python", "pkgconf"]), "missing"), set())

    def test_missing_formula_is_drift(self):
        found = findings_for(["bat"])
        self.assertEqual(subjects(found, "missing"), {"bat"})
        self.assertTrue(all(f.drift for f in found if f.kind == "missing"))

    def test_missing_cask_is_drift(self):
        self.assertEqual(subjects(findings_for(expected_casks=["zulu@17"]), "missing"), {"zulu@17"})

    def test_installed_replaced_package_names_its_replacement(self):
        found = [f for f in findings_for() if f.kind == "replaced" and f.subject == "tldr"]
        self.assertEqual(len(found), 1)
        self.assertIn("tlrc", found[0].detail)
        self.assertTrue(found[0].drift)

    def test_dropped_package_has_no_replacement(self):
        found = [f for f in findings_for() if f.kind == "replaced" and f.subject == "quicklook-csv"]
        self.assertEqual(len(found), 1)
        self.assertIn("no replacement", found[0].detail)

    def test_replaced_package_is_not_also_reported_as_flagged(self):
        self.assertNotIn("tldr", subjects(findings_for(), "flagged"))

    def test_renamed_cask_installed_under_new_token_is_clean(self):
        found = findings_for(expected_casks=["docker-desktop"])
        self.assertNotIn("docker", subjects(found, "replaced"))
        self.assertNotIn("docker-desktop", subjects(found, "missing"))

    def test_flagged_package_outside_setup_is_info_only(self):
        found = [f for f in findings_for() if f.subject == "macdown"]
        self.assertEqual([f.kind for f in found], ["flagged"])
        self.assertFalse(found[0].drift)


class SkipListTest(unittest.TestCase):
    def test_skip_list_ignores_comments_and_blanks(self):
        text = "# apps I don't use\nchatgpt\n\n  daisydisk  # disk viewer\n"
        self.assertEqual(setup.parse_skip(text), {"chatgpt", "daisydisk"})

    def test_missing_skip_file_skips_nothing(self):
        self.assertEqual(setup.parse_skip(None), set())

    def test_skipped_package_is_not_reported_missing(self):
        index = setup.installed_index(BREW)
        found = setup.package_findings(set(), {"chatgpt", "zulu@17"}, setup.REPLACED, index, skip={"chatgpt"})
        self.assertEqual(subjects(found, "missing"), {"zulu@17"})


class ZshrcFindingsTest(unittest.TestCase):
    def test_current_block_is_clean(self):
        self.assertEqual(setup.zshrc_findings("# mine\n" + setup.ZSHRC_BLOCK), [])

    def test_legacy_nvmrc_hook_is_drift(self):
        legacy = 'load-nvmrc() {\n  local nvmrc_path="$(nvm_find_nvmrc 2>/dev/null)"\n}\n'
        found = setup.zshrc_findings(setup.ZSHRC_BLOCK + legacy)
        self.assertEqual(len(found), 1)
        self.assertIn("nvm_find_nvmrc", found[0].detail)
        self.assertTrue(found[0].drift)

    def test_missing_markers_are_each_reported(self):
        found = setup.zshrc_findings("# empty\n")
        self.assertEqual(len(found), len(setup.ZSHRC_MARKERS))
        self.assertTrue(all(f.drift for f in found))


class SettingFindingsTest(unittest.TestCase):
    def test_nvm_default_stable_is_drift(self):
        self.assertTrue(setup.nvm_alias_findings("stable\n")[0].drift)

    def test_nvm_default_lts_is_clean(self):
        self.assertEqual(setup.nvm_alias_findings("lts/*\n"), [])

    def test_nvm_default_unset_is_drift(self):
        self.assertTrue(setup.nvm_alias_findings(None)[0].drift)

    def test_older_ruby_is_info_only(self):
        found = setup.ruby_findings("3.4.8")
        self.assertEqual(len(found), 1)
        self.assertFalse(found[0].drift)

    def test_current_ruby_is_clean(self):
        self.assertEqual(setup.ruby_findings(setup.RUBY_VERSION), [])

    def test_rsa_only_ssh_key_is_info_and_never_fixable(self):
        found = setup.ssh_findings(["id_rsa"])
        self.assertEqual(len(found), 1)
        self.assertFalse(found[0].drift)
        self.assertIsNone(found[0].fix)

    def test_ed25519_key_is_clean(self):
        self.assertEqual(setup.ssh_findings(["id_rsa", "id_ed25519"]), [])


if __name__ == "__main__":
    unittest.main()
