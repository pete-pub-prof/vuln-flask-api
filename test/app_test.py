import unittest

from app import UserDatabase


class AppDatabaseTest(unittest.TestCase):
    def smoke_test_database(self):
        with UserDatabase("test.db") as db:
            db.add_user("admin1", "admin-password-1")
            db.add_user("user1", "user-password-1")
            db.add_user("user2", "user-password-2")
            db._print_users()

    def test_create_user_database(self):
       pass
    def test_add_user(self):
        with UserDatabase("test_add_user.db") as db:
            db.add_user("admin1", "admin-password-1")
            rows = db.cursor.execute("SELECT * from user;").fetchall()
            self.assertEqual(len(rows), 1)
            (user_id, username, _) = rows[0]
            self.assertEqual(1, user_id)
            self.assertEqual(username, "admin1")

    def test_get_authenticated_user_success(self):
        expected_username = "admin1"
        password = "admin-password-1"
        with UserDatabase("test_auth_success.db") as db:
            db.add_user(expected_username, password)
            db.add_user("user1", "user-password-1")
            db.add_user("user2", "user-password-2")

            user = db.get_authenticated_user(expected_username, password)
            self.assertEqual(user.username, expected_username)

    def test_get_authenticated_user_fail(self):
        expected_username = "admin1"
        password = "admin-password-1"
        with UserDatabase("test_auth_fail.db") as db:
            db.add_user(expected_username, password)
            db.add_user("user1", "user-password-1")
            db.add_user("user2", "user-password-2")

            has_value_error = False
            try:
                _user = db.get_authenticated_user(expected_username, "not-the-right-password")
            except ValueError:
                has_value_error = True
            self.assertTrue(has_value_error)

if __name__ == '__main__':
    unittest.main()
