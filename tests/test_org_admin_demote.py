from argparse import ArgumentParser, Namespace
import importlib.util
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import call, patch

SCRIPT_PATH = Path(__file__).parents[1] / "org-admin-demote.py"
sys.path.insert(0, str(SCRIPT_PATH.parent))
SPEC = importlib.util.spec_from_file_location("org_admin_demote", SCRIPT_PATH)
assert SPEC is not None
assert SPEC.loader is not None
org_admin_demote = importlib.util.module_from_spec(SPEC)
try:
    SPEC.loader.exec_module(org_admin_demote)
finally:
    sys.path.pop(0)


def parse_args(*args: str) -> Namespace:
    parser = ArgumentParser()
    org_admin_demote.add_args(parser)
    return parser.parse_args(["enterprise-slug", *args])


class OrgAdminDemoteTests(TestCase):
    def test_target_role_defaults_to_unaffiliated(self) -> None:
        self.assertEqual(parse_args().target_role, "unaffiliated")

    def test_main_processes_only_org_ids_from_unmanaged_file(self) -> None:
        with TemporaryDirectory() as temp_dir:
            unmanaged_orgs = Path(temp_dir) / "unmanaged_orgs.txt"
            unmanaged_orgs.write_text("org-id-1\n\norg-id-2\n", encoding="utf-8")

            with (
                patch.object(
                    sys,
                    "argv",
                    [
                        "org-admin-demote.py",
                        "enterprise-slug",
                        "--unmanaged-orgs",
                        str(unmanaged_orgs),
                        "--target-role",
                        "member",
                    ],
                ),
                patch.object(
                    org_admin_demote.util, "read_token", return_value="test-token"
                ),
                patch.object(
                    org_admin_demote.util, "validate_ca_bundle", return_value=True
                ),
                patch.object(
                    org_admin_demote.enterprises,
                    "get_enterprise_id",
                    return_value="enterprise-id",
                ),
                patch.object(
                    org_admin_demote.enterprises, "promote_admin"
                ) as promote_admin,
            ):
                org_admin_demote.main()

        self.assertEqual(
            promote_admin.call_args_list,
            [
                call(
                    "https://api.github.com/graphql",
                    {"Authorization": "token test-token"},
                    "enterprise-id",
                    "org-id-1",
                    "DIRECT_MEMBER",
                    verify=True,
                ),
                call(
                    "https://api.github.com/graphql",
                    {"Authorization": "token test-token"},
                    "enterprise-id",
                    "org-id-2",
                    "DIRECT_MEMBER",
                    verify=True,
                ),
            ],
        )

    def test_demote_admin_defaults_to_unaffiliated(self) -> None:
        with patch.object(
            org_admin_demote.enterprises, "promote_admin"
        ) as promote_admin:
            org_admin_demote.demote_admin(
                "https://api.github.com/graphql",
                {"Authorization": "token test"},
                "enterprise-id",
                ["org-id"],
            )

        promote_admin.assert_called_once_with(
            "https://api.github.com/graphql",
            {"Authorization": "token test"},
            "enterprise-id",
            "org-id",
            "UNAFFILIATED",
            verify=True,
        )

    def test_demote_admin_uses_requested_target_role(self) -> None:
        roles = [
            ("unaffiliated", "UNAFFILIATED"),
            ("member", "DIRECT_MEMBER"),
        ]
        for target_role, graphql_role in roles:
            with self.subTest(target_role=target_role):
                with patch.object(
                    org_admin_demote.enterprises, "promote_admin"
                ) as promote_admin:
                    org_admin_demote.demote_admin(
                        "https://api.github.com/graphql",
                        {"Authorization": "token test"},
                        "enterprise-id",
                        ["org-id-1", "org-id-2"],
                        verify="ca.pem",
                        target_role=target_role,
                    )

                self.assertEqual(
                    promote_admin.call_args_list,
                    [
                        call(
                            "https://api.github.com/graphql",
                            {"Authorization": "token test"},
                            "enterprise-id",
                            "org-id-1",
                            graphql_role,
                            verify="ca.pem",
                        ),
                        call(
                            "https://api.github.com/graphql",
                            {"Authorization": "token test"},
                            "enterprise-id",
                            "org-id-2",
                            graphql_role,
                            verify="ca.pem",
                        ),
                    ],
                )
