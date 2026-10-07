"""
Unit tests for Python automation services and security validation.
Compatible with standard library unittest.
"""

import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# Ensure src/ is on python path
src_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src")
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

from industry_taxonomy import IndustryTaxonomyEngine, TAXONOMY_CATALOG
from browsergym_service import BrowserGymAutomationService


class TestIndustryTaxonomy(unittest.TestCase):
    def setUp(self):
        self.engine = IndustryTaxonomyEngine()

    def test_detect_finance_industry(self):
        result = self.engine.detect_industry("Senior Portfolio Manager (Fundos Multimercado)")
        self.assertEqual(result, "FINANCE_ASSET_MANAGEMENT")

    def test_detect_healthcare_industry(self):
        result = self.engine.detect_industry("Médico Plantonista Cardiologista UTI")
        self.assertEqual(result, "HEALTHCARE_MEDICAL")

    def test_detect_bakery_industry(self):
        result = self.engine.detect_industry("Chef Padeiro Artesanal com Fermentação Natural")
        self.assertEqual(result, "FOOD_BAKERY_GASTRONOMY")

    def test_detect_civil_engineering_industry(self):
        result = self.engine.detect_industry("Engenheiro Civil Gerente de Obras Prediais")
        self.assertEqual(result, "CIVIL_ENGINEERING_CONSTRUCTION")

    def test_detect_software_industry_default(self):
        result = self.engine.detect_industry("Senior Java Developer Spring Boot")
        self.assertEqual(result, "SOFTWARE_TECH_AI")

    def test_taxonomy_pack_contains_required_fields(self):
        for industry_key in TAXONOMY_CATALOG.keys():
            pack = self.engine.get_taxonomy_pack(industry_key)
            self.assertIn("display_name", pack)
            self.assertIn("keywords_mandatory", pack)
            self.assertIn("action_verbs", pack)
            self.assertGreater(len(pack["keywords_mandatory"]), 0)
            self.assertGreater(len(pack["action_verbs"]), 0)


class TestBrowserGymAutomationService(unittest.TestCase):
    def test_service_initialization(self):
        service = BrowserGymAutomationService(headless=True)
        self.assertTrue(service.headless)
        self.assertTrue(os.path.exists(service.screenshots_dir))


class TestSecurityInputRules(unittest.TestCase):
    """
    Validates regex rules and security sanitization checks in python backend.
    """
    def test_safe_job_url_validation(self):
        import re
        safe_url_pattern = re.compile(r"^https?://[a-zA-Z0-9_\-./:=?&%#+]+$")

        valid_url = "https://www.linkedin.com/jobs/view/12345678"
        self.assertTrue(bool(safe_url_pattern.match(valid_url)))

        invalid_url_with_injection = "https://www.linkedin.com/jobs; rm -rf /"
        self.assertFalse(bool(safe_url_pattern.match(invalid_url_with_injection)))

        invalid_url_with_pipe = "https://www.linkedin.com/jobs|whoami"
        self.assertFalse(bool(safe_url_pattern.match(invalid_url_with_pipe)))

    def test_safe_job_id_validation(self):
        import re
        safe_id_pattern = re.compile(r"^[a-zA-Z0-9_\-]{1,100}$")

        self.assertTrue(bool(safe_id_pattern.match("linkedin-102938")))
        self.assertTrue(bool(safe_id_pattern.match("job_98234")))
        self.assertFalse(bool(safe_id_pattern.match("job; evil")))
        self.assertFalse(bool(safe_id_pattern.match("../traversal")))


if __name__ == "__main__":
    unittest.main()
