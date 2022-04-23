"""Message model tests."""

# run these tests like:
#
#    python -m unittest test_message_model.py


import os
from unittest import TestCase, expectedFailure
import unittest

from models import db, User, Message, Follows, Likes

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"


# Now we can import app

from app import app

db.create_all()

class MessageModelTestCase(TestCase):
    """Test model for messages."""

    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        Message.query.delete()
        Follows.query.delete()

        u = User(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD"
        )

        u1 = User(
            email="test1@test.com",
            username="testuser1",
            password="HASHED_PASSWORD"
        )

        db.session.add(u)
        db.session.add(u1)
        db.session.commit()

        self.u_id = u.id
        self.u = u
        self.u1_id = u1.id
        self.u1 = u1

        msg = Message(
            text="test message",
            user_id=self.u_id)

        db.session.add(msg)
        db.session.commit()

        self.msg_id = msg.id
        self.msg = msg

    def tearDown(self):
        """Clean up any fouled transaction."""

        db.session.rollback()

    def test_msg_model(self):
        """Test basic model works."""

        self.assertEqual(self.msg.text, "test message")
        self.assertIsInstance(self.msg, Message)
        

    def test_user_has_message(self):
        """Test Message populates in User."""

        self.assertEqual(len(self.u.messages), 1)
        self.assertIn(self.msg, self.u.messages)
        self.assertEqual(self.msg.user_id, self.u_id)

    def test_msg_like(self):
        """Test message like"""

        like = Likes(user_id=self.u1_id, message_id=self.msg_id)

        db.session.add(like)
        db.session.commit()

        self.assertIsInstance(like, Likes)
        self.assertIsInstance(like.id, int)

    def test_msg_in_likes(self):
        """Test liked message in user likes."""

        like = Likes(user_id=self.u1_id, message_id=self.msg_id)
        db.session.add(like)
        db.session.commit()

        self.like_id = like.id
        self.like = like

        self.assertIn(self.msg, self.u1.likes)
        self.assertEqual(self.msg, self.u1.likes[0])

    class ExpectedFailureTestCase(TestCase):
        @unittest.expectedFailure

        def test_message_fail(self):
            """Test new message validation fails."""

            failed_msg = Message(text="failed message")
            db.session.add(failed_msg)
            db.session.commit()

            self.assertIsInstance(failed_msg, Message)

        def test_like_fail(self):
            """Test user cannot like own message."""

            failed_like = Likes(user_id=self.u_id, message_id=self.msg_id)
            db.session.add(failed_like)
            db.session.commit()

            self.assertNotIsInstance(failed_like, Likes)


# FLASK_ENV=production python -m unittest test_message_model.py
