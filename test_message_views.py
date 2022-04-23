"""Message View tests."""

# run these tests like:
#
#    FLASK_ENV=production python -m unittest test_message_views.py


import os
from unittest import TestCase, expectedFailure
import unittest

from models import db, connect_db, Message, User

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"


# Now we can import app

from app import app, CURR_USER_KEY

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()

# Don't have WTForms use CSRF at all, since it's a pain to test

app.config['WTF_CSRF_ENABLED'] = False


class MessageViewTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        Message.query.delete()

        self.client = app.test_client()

        self.testuser = User.signup(username="testuser",
                                    email="test@test.com",
                                    password="testuser",
                                    image_url=None)

        testuser2 = User(
            username="testuser2",
            email="test2@test.com",
            password="testuser",
            image_url=None)

        db.session.add(testuser2)
        db.session.commit()

        self.u2_id = testuser2.id
        self.u2 = testuser2

    def tearDown(self):
        """Cleanup any fouled transactions."""

        db.session.rollback()

    def test_add_message(self):
        """Can user add a message?"""

        # Since we need to change the session to mimic logging in,
        # we need to use the changing-session trick:

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            # Now, that session setting is saved, so we can have
            # the rest of ours test

            resp = c.post("/messages/new", data={"text": "Hello"})

            # Make sure it redirects
            self.assertEqual(resp.status_code, 302)

            msg = Message.query.one()
            self.assertEqual(msg.text, "Hello")

    def test_add_message_redirects(self):
        """Is user redirected to user page with new message?"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            resp = c.post("/messages/new", data={"text": "Hello"}, follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Hello", html)
            self.assertIn(self.testuser.username, html)

    def test_no_user_new_message(self):
        """Test if anon user can make new message."""

        resp = self.client.post("/messages/new", data={"text": "Hello"}, follow_redirects=True)
        html = resp.get_data(as_text=True)

        self.assertEqual(resp.status_code, 200)
        self.assertIn("Access unauthorized.", html)
        

    def test_delete_message(self):
        """Can logged in user delete their owm message?"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            msg = Message(text="Test", user_id=self.testuser.id)
            db.session.add(msg)
            db.session.commit()

            resp = c.post(f"/messages/{msg.id}/delete", follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn(self.testuser.username, html)
            self.assertNotIn(msg.text, html)

    def test_no_user_delete_message(self):
        """Test anon user cannot delete a message."""

        msg = Message(text="Test", user_id=self.testuser.id)
        db.session.add(msg)
        db.session.commit()

        resp = self.client.post(f"/messages/{msg.id}/delete", follow_redirects=True)
        html = resp.get_data(as_text=True)

        self.assertEqual(resp.status_code, 200)
        self.assertIn("Access unauthorized.", html)

    class ExpectedFailureTestCase(TestCase):
        @unittest.expectedFailure

        def test_delete_other_user_message(self):
            """Is user prohibited from deleting another user's message?"""

            msg = Message(
            text="test message",
            user_id=self.u2_id)

            db.session.add(msg)
            db.session.commit()

            with self.client as c:
                with c.session_transaction() as sess:
                    sess[CURR_USER_KEY] = self.testuser.id

                resp = c.post(f"/messages/{msg.id}/delete",     follow_redirects=True)
                html = resp.get_data(as_text=True)

                self.assertEqual(resp.status_code, 200)
                self.assertIn("test message.", html)

        def test_add_message_as_other_user(self):
            """Can a logged in user add a message as another user?"""

            with self.client as c:
                with c.session_transaction() as sess:
                    sess[CURR_USER_KEY] = self.testuser.id

                resp = c.post("/messages/add", data={"text": "Goodbye", "user_id": f"{self.u2_id}"}, follow_redirects=True)
                html = resp.get_data(as_Text=True)

                self.assertEqual(resp.status_code, 200)
                self.assertIn("Goodbye", html)

