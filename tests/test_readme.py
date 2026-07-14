from pathlib import Path
import unittest
import yaml


ROOT = Path(__file__).resolve().parents[1]


class ReadmeTests(unittest.TestCase):
    def test_readmes_document_penalty_without_score_cap(self):
        english = (ROOT / "README.md").read_text(encoding="utf-8")
        chinese = (ROOT / "README.zh-CN.md").read_text(encoding="utf-8")
        self.assertIn("10-20", english)
        self.assertIn("10–20", chinese)
        self.assertNotIn("score is capped at 30", english)
        self.assertNotIn("限制在 30", chinese)

    def test_workflow_serializes_scans(self):
        workflow = (ROOT / ".github/workflows/daily.yml").read_text(encoding="utf-8")
        self.assertIn("concurrency:", workflow)
        self.assertIn("cancel-in-progress: false", workflow)

    def test_optional_agents_are_documented_and_persisted_safely(self):
        english = (ROOT / "README.md").read_text(encoding="utf-8")
        chinese = (ROOT / "README.zh-CN.md").read_text(encoding="utf-8")
        workflow = (ROOT / ".github/workflows/daily.yml").read_text(encoding="utf-8")
        env_example = (ROOT / ".env.example").read_text(encoding="utf-8")
        for name in ("ENABLE_COMPANY_INTEL", "MAX_INTEL_CALLS", "COMPANY_INTEL_TTL_DAYS"):
            self.assertIn(name, english)
            self.assertIn(name, chinese)
            self.assertIn(name, workflow)
            self.assertIn(name, env_example)
        self.assertIn("python -m src.agents.draft --list", english)
        self.assertIn("python -m src.agents.draft --list", chinese)
        self.assertIn("disabled by default", english)
        self.assertIn("默认关闭", chinese)
        self.assertIn("if: always()", workflow)
        self.assertIn("data/matches.json data/company_intel.json", workflow)
        self.assertIn("persist-credentials: false", workflow)
        self.assertIn("GH_TOKEN: ${{ github.token }}", workflow)
        self.assertIn("Public repositories expose", english)
        self.assertIn("日常岗位判断也会", chinese)
        self.assertIn("source .env", english)
        self.assertIn("source .env", chinese)

    def test_community_documents_and_current_defaults_are_documented(self):
        english = (ROOT / "README.md").read_text(encoding="utf-8")
        chinese = (ROOT / "README.zh-CN.md").read_text(encoding="utf-8")
        self.assertTrue((ROOT / "CONTRIBUTING.md").exists())
        self.assertTrue((ROOT / "SECURITY.md").exists())
        self.assertIn("Top 10", english)
        self.assertNotIn("add two secrets", english)
        self.assertNotIn("填两个 secret", chinese)

    def test_project_uses_descriptive_brand(self):
        english = (ROOT / "README.md").read_text(encoding="utf-8")
        email = (ROOT / "src/notify/email.py").read_text(encoding="utf-8")
        self.assertTrue(english.startswith("# English Job Agent for Germany"))
        self.assertIn("No German Required? Check before you apply.", english)
        self.assertIn("[English Job Agent for Germany]", email)
        for relative in ("README.md", "README.zh-CN.md", "CONTRIBUTING.md", "LICENSE", "src/main.py", "src/notify/email.py"):
            self.assertNotIn("no-german-required", (ROOT / relative).read_text(encoding="utf-8"))

    def test_new_public_ats_families_are_configured_and_documented(self):
        companies = yaml.safe_load((ROOT / "data/companies.yaml").read_text(encoding="utf-8"))["companies"]
        counts = {ats: sum(company.get("ats") == ats for company in companies)
                  for ats in ("personio", "smartrecruiters", "recruitee")}
        self.assertEqual(counts, {"personio": 4, "smartrecruiters": 3, "recruitee": 3})
        main = (ROOT / "src/main.py").read_text(encoding="utf-8")
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        for name in ("Personio", "SmartRecruiters", "Recruitee"):
            self.assertIn(f"{name}Source", main)
            self.assertIn(name, readme)


if __name__ == "__main__":
    unittest.main()
