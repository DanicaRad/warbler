"""User model tests."""

# run these tests like:
#
#    python -m unittest test_user_model.py


import os
from unittest import TestCase, expectedFailure
import unittest

from models import db, User, Message, Follows

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"


# Now we can import app

from app import app

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()


class UserModelTestCase(TestCase):
    """Test model for users."""

    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        Message.query.delete()
        Follows.query.delete()

        u1 = User(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD"
        )

        u2 = User(
            email="test2@test.com",
            username="testuser2",
            password="HASHED_PASSWORD"
        )

        db.session.add(u1)
        db.session.add(u2)
        db.session.commit()

        self.u1_id = u1.id
        self.u2_id = u2.id
        self.u1 = u1
        self.u2 = u2

        m1 = Message(
            text="Message 1",
            user_id=self.u1_id
            )

        m2 = Message(
            text="Message 2",
            user_id=self.u2_id
        )

        db.session.add(m1)
        db.session.add(m2)
        db.session.commit()

        self.m1_id = m1.id
        self.m2_id = m2.id
        self.m1 = m1
        self.m2 = m2

        f = Follows(
            user_being_followed_id=self.u1_id,
            user_following_id=self.u2_id
        )

        db.session.add(f)
        db.session.commit()

        self.client = app.test_client()

    def tearDown(self):
        """Clean up any fouled transaction."""

        db.session.rollback()

    def test_user_model(self):
        """Does basic model work?"""

        self.assertEqual(len(self.u1.messages), 1)
        self.assertEqual(len(self.u1.followers), 1)

    def test_is_following(self):
        """Test User.is_following()"""

        self.assertTrue(self.u2.is_following(self.u1))
        self.assertFalse(self.u1.is_following(self.u2))

    def test_is_followed_by(self):
        """Test User.is_followed_by()"""

        self.assertTrue(self.u1.is_followed_by(self.u2))
        self.assertFalse(self.u2.is_followed_by(self.u1))

    def test_user_signup(self):
        """Test User.signup successfully creates new credentialed user"""

        u3 = User.signup("testuser3", "test3@test.com", "HASHED_PASSWORD", User.image_url.default.arg)

        self.assertIsInstance(u3, User)
        self.assertEqual(f"{u3}", f"<User #{u3.id}: testuser3, test3@test.com>")

    def test_user_login(self):
        """Test User.authenticate"""

        u3 = User.signup("testuser3", "test3@test.com", "HASHED_PASSWORD", User.image_url.default.arg)

        self.assertEqual(User.authenticate
                        ("testuser3", 
                        "HASHED_PASSWORD"),
                        u3)
        self.assertFalse(User.authenticate("testuser3", "sofghijjn"))


class ExpectedFailureTestCase(TestCase):
    @unittest.expectedFailure

    def test_user_signup_fail(self):
        """Test User.signup fails if validations fail"""

        u4 = User.signup("testuser4", "HASHED_PASSWORD")
        u5 = User.signup("testuser5", "test3@test.com", "HASED_PASSWORD")

        self.assertFalse(u4)
        self.assertFalse(u5)
