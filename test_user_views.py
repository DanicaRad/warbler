"""User View tests."""

# run these tests like:
#
#    FLASK_ENV=production python -m unittest test_user_views.py


import os
from unittest import TestCase
from flask import session
from models import db, connect_db, Message, User, Likes, Follows

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"

from app import app, CURR_USER_KEY


db.create_all()

app.config['WTF_CSRF_ENABLED'] = False


class UserViewTestCase(TestCase):
    """Test views for users."""

    def setUp(self):
        """Create test client, add sample data."""

        Follows.query.delete()
        User.query.delete()
        Likes.query.delete()
        Message.query.delete()

        self.client = app.test_client()

        self.testuser = User.signup(username="testuser",
                                    email="test@test.com",
                                    password="testuser",
                                    image_url=None)

        testuser2 = User(
            username="testuser2",
            password="testuser2",
            email="test2@test.com"
        )
        db.session.add(testuser2)
        db.session.commit()

        self.u2_id = testuser2.id
        self.u2 = testuser2

    def test_view_signup_form(self):
        """Does user signup form show if no logged in user?"""

        resp = self.client.get("/signup")
        html = resp.get_data(as_text=True)

        self.assertEqual(resp.status_code, 200)
        self.assertIn("Join Warbler today.", html)


    def test_add_user(self):
        """Can new user sign up?"""

        resp = self.client.post("/signup", data={
            "username": "newtestuser",
            "password": "newtestuser",
            "email": "newtest@test.com"
        }, follow_redirects=True)
        html = resp.get_data(as_text=True)

        self.assertEqual(resp.status_code, 200)
        self.assertIn("newtestuser", html)

    def test_show_login(self):
        """Does login form show when no logged in user?"""

        resp = self.client.get("/login")
        html = resp.get_data(as_text=True)

        self.assertEqual(resp.status_code, 200)
        self.assertIn("Welcome back.", html)

    def test_login(self):
        """Can user login and add to session?"""

        resp = self.client.post("/login", data={
            "username": "testuser",
            "password": "testuser"
        }, follow_redirects=True)
        html = resp.get_data(as_text=True)

        self.assertEqual(resp.status_code, 200)
        self.assertIn("Hello, testuser!", html)

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            self.assertEqual(self.testuser.id, sess[CURR_USER_KEY])

    def test_logout_view(self):
        """Test logout redirects to login"""

        resp = self.client.get("/logout", follow_redirects=True)
        html = resp.get_data(as_text=True)

        self.assertEqual(resp.status_code, 200)
        self.assertIn("Welcome back.", html)

    def test_all_users_view(self):
        """Test all users view"""

        resp = self.client.get("/users")
        html = resp.get_data(as_text=True)

        self.assertEqual(resp.status_code, 200)
        self.assertIn("testuser", html)

    def test_search_users_view(self):
        """Does search user retrun user?"""

        resp = self.client.get("/users?q=testuser")
        html = resp.get_data(as_text=True)

        self.assertEqual(resp.status_code, 200)
        self.assertIn("testuser", html)

    def test_user_profile(self):
        """Test user profile view"""

        resp = self.client.get(f"/users/{self.testuser.id}")
        html = resp.get_data(as_text=True)

        self.assertEqual(resp.status_code, 200)
        self.assertIn("Messages", html)
        self.assertIn("Following", html)
        self.assertIn("@testuser", html)

    def test_see_following_logged_in(self):
        """Can logged in user see who a user is following?"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            resp = c.get(f"/users/{self.u2_id}/following")
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("testuser2", html)

    def test_see_following_anon(self):
        """Is anon user prohibited from seeing who another user is following?"""

        resp = self.client.get(f"/users/{self.testuser.id}/following", follow_redirects=True)
        html = resp.get_data(as_text=True)

        self.assertEqual(resp.status_code, 200)
        self.assertIn("Access unauthorized.", html)
        self.assertNotIn("testuser", html)

    def test_see_followers(self):
        """Can logged in user see another user's followers?"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            resp = c.get(f"/users/{self.u2_id}/followers")
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("testuser2", html)
            self.assertIn("Followers", html)

    def test_see_followers_anon(self):
        """Is anon user prohibited from seeing another user's followers?"""
        resp = self.client.get(f"/users/{self.testuser.id}/followers", follow_redirects=True)
        html = resp.get_data(as_text=True)

        self.assertEqual(resp.status_code, 200)
        self.assertIn("Access unauthorized.", html)
        self.assertNotIn("testuser", html)

    def test_view_likes(self):
        """Can logged in user see another user's likes?"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            resp = c.get(f"/users/{self.u2_id}/likes")
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("@testuser2\'s</a> liked Warbles", html)

    def test_anon_view_likes(self):
        """Can anon user view another user's likes?"""

        resp = self.client.get(f"/users/{self.testuser.id}/likes", follow_redirects=True)
        html = resp.get_data(as_text=True)

        self.assertEqual(resp.status_code, 200)
        self.assertIn("testuser", html)

    def test_add_follow_unfollow(self):
        """Can logged in user follow and unfollow another user?"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            resp = c.post(f"/users/follow/{self.u2_id}", follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("testuser2", html)

            resp2 = c.post(f"/users/stop-following/{self.u2_id}", follow_redirects=True)
            html2 = resp2.get_data(as_text=True)

            self.assertEqual(resp2.status_code, 200)
            self.assertNotIn("testuser2", html2)

    def test_show_edit_profile_form(self):
        """Can logged in user view form to edit profile?"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            resp = c.get("/users/profile")
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Edit Your Profile.", html)

    def test_edit_profile_submit(self):
        """Can logged in user edit their profile?"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            resp = c.post("/users/profile", data={
                    "username": "testuser",
                    "email": "test@test.com",
                    "bio": "New bio!",
                    "password": "testuser"},
                    follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("New bio!", html)

    def test_wrong_password_edit_profile(self):
        """Is user prohibited from editing profile with incorrect password?"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            resp = c.post("/users/profile", data={
                    "username": "testuser",
                    "email": "test@test.com",
                    "bio": "New bio!",
                    "password": "wrongpassword"},
                    follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized; incorrect password.", html)

    def test_prohibit_edit_other_profile(self):
        """Is user prohibited from editing another user's profile?"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            resp = c.post("/users/profile", data={
                    "username": "testuser2",
                    "email": "test2@test.com",
                    "bio": "New bio!",
                    "password": "testuser2"},
                    follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized", html)

    def test_delete_user(self):
        """Can logged in user delete their profile?"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            resp = c.post("/users/delete", follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Profile deleted.", html)
            self.assertIn("Join Warbler today.", html)

    def like_message(self):
        """Can a user like another user's message?"""

        msg = Message(text="test message", user_id=self.u2_id)
        db.session.add(msg)
        db.session.commit()
        self.msg_id = msg.id

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            resp = c.post(f"/users/add_like/{self.msg_id}", follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Message added to likes!", html)

    def test_like_own_message(self):
        """Is user prohibited from liking their own message?"""

        msg = Message(text="test message", user_id=self.testuser.id)
        db.session.add(msg)
        db.session.commit()

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            resp = c.post(f"/users/add_like/{msg.id}", follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertNotIn("Message added to likes!", html)

    def test_logged_in_homepage(self):
        """Test homepage view if logged in."""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            resp = c.get("/")
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("testuser", html)
            self.assertIn("Following", html)

    def test_home_anon(self):
        """Test homepage if anon user"""

        resp = self.client.get("/")
        html = resp.get_data(as_text=True)

        self.assertEqual(resp.status_code, 200)
        self.assertIn("What's Happening?", html)