from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import sqlite3
import tempfile
import threading
import unittest

from redeemer.db import Database


class CodeScopesTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Database(Path(self.tmp.name) / 'test.db')
        for slug in ('alpha', 'beta', 'gamma'):
            self.db.add_app(slug, slug.title())

    def tearDown(self):
        self.db.close()
        self.tmp.cleanup()

    def test_same_text_has_independent_limits_history_and_actions(self):
        first = self.db.add_code('WELCOME', 'alpha', max_uses=1)
        second = self.db.add_code('welcome', 'beta', max_uses=2)
        self.assertNotEqual(first, second)
        self.assertEqual(self.db.redeem('alpha', 'WELCOME', 'd1'), (True, 'ok'))
        self.assertEqual(self.db.redeem('beta', 'WELCOME', 'd1'), (True, 'ok'))
        self.assertEqual(self.db.redeem('alpha', 'WELCOME', 'd2'), (False, 'exhausted'))
        self.assertEqual(self.db.redeem('beta', 'WELCOME', 'd2'), (True, 'ok'))
        self.assertEqual(self.db.code(first)['uses'], 1)
        self.assertEqual(self.db.code(second)['uses'], 2)
        self.assertEqual({r['app_slug'] for r in self.db.redemptions(code=first)}, {'alpha'})
        self.db.set_enabled(first, False)
        self.assertEqual(self.db.code(second)['enabled'], 1)
        self.db.delete_code(first)
        self.assertEqual(len(self.db.redemptions(code=second)), 2)
        self.assertEqual(self.db.conn.execute('PRAGMA foreign_key_check').fetchall(), [])

    def test_overlapping_assignments_and_globals_rejected_atomically(self):
        self.db.add_code('WELCOME', app_slugs=['alpha', 'beta'])
        for scope in ({'app_slugs': ['beta', 'gamma']}, {}, {'app_slug': 'alpha'}):
            with self.assertRaises(ValueError):
                self.db.add_code('wel come', **scope)
        self.assertEqual(self.db.totals()['codes'], 1)
        self.db.add_code('WELCOME', 'gamma')
        self.db.add_code('GLOBAL', None)
        for scope in ({}, {'app_slug': 'alpha'}, {'app_slugs': ['beta', 'gamma']}):
            with self.assertRaises(ValueError):
                self.db.add_code('GLOBAL', **scope)
        self.assertEqual(self.db.totals()['codes'], 3)

    def test_invalid_scope_and_quota_leave_no_code(self):
        for options in ({'app_slugs': []}, {'app_slugs': ['alpha', 'missing']},
                        {'quota_mode': 'invalid'}, {'max_uses': 0}):
            with self.assertRaises(ValueError):
                self.db.add_code('INVALID', **options)
        self.assertEqual(self.db.totals()['codes'], 0)

    def test_shared_and_per_app_quotas_for_selected_and_global(self):
        for global_scope in (False, True):
            for mode in ('shared', 'per_app'):
                with self.subTest(global_scope=global_scope, mode=mode):
                    text = f'TEST-{int(global_scope)}-{mode.replace("_", "-").upper()}'
                    options = {} if global_scope else {'app_slugs': ['alpha', 'beta']}
                    code_id = self.db.add_code(text, max_uses=1, quota_mode=mode, **options)
                    self.assertEqual(self.db.redeem('alpha', text, 'same'), (True, 'ok'))
                    self.assertEqual(self.db.redeem('alpha', text, 'same'), (True, 'already'))
                    self.assertEqual(self.db.redeem('alpha', text, 'other'), (False, 'exhausted'))
                    expected = (True, 'ok') if mode == 'per_app' else (False, 'exhausted')
                    self.assertEqual(self.db.redeem('beta', text, 'same'), expected)
                    self.assertEqual(self.db.redeem('missing', text), (False, 'unknown_app'))
                    if not global_scope:
                        self.assertEqual(self.db.redeem('gamma', text), (False, 'wrong_app'))
                    self.assertEqual(self.db.code(code_id)['uses'], 2 if mode == 'per_app' else 1)

    def test_future_apps_receive_globals_only_and_individual_quota(self):
        self.db.add_code('GLOBAL', quota_mode='per_app', max_uses=1)
        self.db.add_code('CHOSEN', app_slugs=['alpha', 'beta'])
        self.db.redeem('alpha', 'GLOBAL')
        self.db.add_app('future', 'Future')
        self.assertEqual(self.db.redeem('future', 'GLOBAL'), (True, 'ok'))
        self.assertEqual(self.db.redeem('future', 'CHOSEN'), (False, 'wrong_app'))
        self.assertEqual({c['code'] for c in self.db.codes('future')}, {'GLOBAL'})

    def test_deleting_app_preserves_shared_code_and_consumed_shared_quota(self):
        shared = self.db.add_code('SHARED', app_slugs=['alpha', 'beta'], max_uses=1)
        single = self.db.add_code('SINGLE', 'alpha')
        global_id = self.db.add_code('GLOBAL')
        self.db.redeem('alpha', 'SHARED')
        self.db.delete_app('alpha')
        self.assertIsNone(self.db.code(single))
        self.assertIsNotNone(self.db.code(global_id))
        self.assertEqual(self.db.code_apps(shared), ['beta'])
        self.assertEqual(self.db.redeem('beta', 'SHARED'), (False, 'exhausted'))
        self.db.delete_app('beta')
        self.assertIsNone(self.db.code(shared))
        self.assertIsNotNone(self.db.code(global_id))

    def test_editing_quota_keeps_consumed_uses(self):
        code_id = self.db.add_code('SHARED', app_slugs=['alpha', 'beta'], max_uses=1)
        self.db.redeem('alpha', 'SHARED')
        self.db.update_code(code_id, note='', max_uses=1, expires_at=None,
                            platforms=None, enabled=True, quota_mode='per_app')
        self.assertEqual(self.db.redeem('beta', 'SHARED'), (True, 'ok'))
        self.assertEqual(self.db.redeem('alpha', 'SHARED'), (False, 'exhausted'))

    def test_backup_round_trip_preserves_assignments_quota_and_history(self):
        code_id = self.db.add_code('SHARED', app_slugs=['alpha', 'beta'], max_uses=1, quota_mode='per_app')
        self.db.redeem('alpha', 'SHARED')
        backup = self.db.backup_to(Path(self.tmp.name) / 'backup.db')
        self.db.delete_code(code_id)
        self.db.restore_from(backup)
        self.assertEqual(self.db.code_apps(code_id), ['alpha', 'beta'])
        self.assertEqual(self.db.redeem('alpha', 'SHARED'), (False, 'exhausted'))
        self.assertEqual(self.db.redeem('beta', 'SHARED'), (True, 'ok'))

    def test_legacy_backup_rejected_without_replacing_database(self):
        old = Path(self.tmp.name) / 'old.db'
        with sqlite3.connect(old) as conn:
            conn.executescript('CREATE TABLE apps(slug TEXT); CREATE TABLE codes(code TEXT); CREATE TABLE redemptions(code TEXT);')
        with self.assertRaises(ValueError):
            self.db.restore_from(old)
        self.assertIsNotNone(self.db.app('alpha'))

    def test_concurrent_creation_cannot_overlap(self):
        barrier = threading.Barrier(2)
        def create():
            try:
                barrier.wait()
                self.db.add_code('SHARED', app_slugs=['alpha', 'beta'])
                return 'created'
            except ValueError:
                return 'duplicate'
            finally:
                self.db.close()
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(lambda _: create(), range(2)))
        self.assertCountEqual(results, ['created', 'duplicate'])
        self.assertEqual(self.db.totals()['codes'], 1)

    def test_concurrent_redemptions_respect_both_quota_modes(self):
        for mode, expected in [('shared', 1), ('per_app', 2)]:
            text = 'RACE-' + mode.replace('_', '-').upper()
            self.db.add_code(text, app_slugs=['alpha', 'beta'], quota_mode=mode, max_uses=1)
            barrier = threading.Barrier(4)
            def redeem(slug):
                try:
                    barrier.wait()
                    return self.db.redeem(slug, text)[0]
                finally:
                    self.db.close()
            with ThreadPoolExecutor(max_workers=4) as pool:
                results = list(pool.map(redeem, ['alpha', 'alpha', 'beta', 'beta']))
            self.assertEqual(sum(results), expected)
