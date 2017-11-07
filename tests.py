import unittest
from main import *

setup_db();

class TestLogin(unittest.TestCase):

    # Ensure that flask was set up correctly
    def test_login_page(self):
        tester = app.test_client(self)
        response = tester.get('/', content_type='html/text')
        self.assertEqual(response.status_code, 200)

    # Ensure that login behaves correctly when logging in as Admin
    def test_login_admin(self):
        tester = app.test_client(self)
        response = tester.post('/', data=dict(zid="1",password="admin123"), follow_redirects = True)
        self.assertIn(b'Admin Dashboard', response.data)

    # Ensure that login behaves correctly when logging in as Staff
    def test_login_staff(self):
        tester = app.test_client(self)
        response = tester.post('/', data=dict(zid="50",password="staff670"), follow_redirects = True)
        self.assertIn(b'Please Confirm Survey', response.data)

    # Ensure that login behaves correctly when logging in as Student
    def test_login_student(self):
        tester = app.test_client(self)
        response = tester.post('/', data=dict(zid="190",password="student123"), follow_redirects = True)
        self.assertIn(b'Survey', response.data)

    # Ensure that login behaves correctly when incorrect login
    def test_login_fail(self):
        tester = app.test_client(self)
        response = tester.post('/', data=dict(zid="1",password="wrong"), follow_redirects = True)
        self.assertIn(b'Invalid Credentials. Please try again.', response.data)

    # Ensure that the index pages requires logins
    def test_index(self):
        tester = app.test_client(self)
        response = tester.get('/index', follow_redirects = True)
        self.assertIn(b'401 Unauthorized', response.data)

class test_create_question(unittest.TestCase):

    # Ensure that admin can access view-questions page
    def test_create_survey(self):
        tester = app.test_client(self)
        tester.post('/', data=dict(zid="1",password="admin123"), follow_redirects = True)
        response = tester.get('/view-question')
        self.assertIn(b'Questions Pool', response.data)

    #Ensure that flask is behaving correctly for view-questions
    def test_view_question_page(self):
        tester = app.test_client(self)
        tester.post('/', data=dict(zid="1",password="admin123"), follow_redirects = True)
        response = tester.get('/view-question')
        self.assertEqual(response.status_code, 200)

    #Ensure staff cannot access view-questions page
    def test_staff_view_questions(self):
        tester = app.test_client(self)
        tester.post('/', data=dict(zid="50",password="staff670"), follow_redirects = True)
        response = tester.get('view-question')
        self.assertIn(b'You are not permitted to access this page!', response.data)

    #Ensure student cannot access view-questions page
    def test_student_view_questions(self):
        tester = app.test_client(self)
        tester.post('/', data=dict(zid="190",password="student123"), follow_redirects = True)
        response = tester.get('view-question')
        self.assertIn(b'You are not permitted to access this page!', response.data)

    # #Ensure a Question can be created and read in the database
    # def test_create_question_into_database(self):
    #     tester = app.test_client(self)
    #     tester.post('/', data=dict(zid="1",password="admin123"), follow_redirects = True)
    #     tester.post('/view-question', data=dict(question="testing question", answer = "sdf"))
    #     response = tester.post('/api/create-question', follow_redirects = True)
    #     self.assertIn(b'testing question', response.data)

class test_enrolment(unittest.TestCase):

    def test_enrol_user_invalid_course(self):
        with app.app_context():
            test_enrolment = "invalid"
            enrolment = Enrolment.query.filter(Enrolment.course_id == test_enrolment).all()
            self.assertEqual(enrolment, [])

    def test_enrol_user_invalid_id(self):
        with app.app_context():
            test_user = 12
            user = Enrolment.query.filter(Enrolment.zid == test_user).all()
            self.assertEqual(user, [])

    def test_enrol_student_valid_id_course(self):
        with app.app_context():
            test_user = 100
            test_course = "COMP9333 17s2"
            course = Enrolment.query.filter(Enrolment.zid == test_user).first().course_id
            self.assertEqual(course, test_course)

    def test_enrol_staff_valid_id_course(self):
        with app.app_context():
            test_user = 80
            test_course = "COMP1000 17s2"
            course = Enrolment.query.filter(Enrolment.zid == test_user).first().course_id
            self.assertEqual(course, test_course)
if __name__ == '__main__':
    unittest.main()
