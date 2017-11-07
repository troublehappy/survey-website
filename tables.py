from server import db
from read_write import *


basedir = os.path.abspath(os.path.dirname(__file__))

class StudentCompletedSurveys(db.Model):
    __tablename__ = "StudentCompletedSurveys"
    key = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer)
    survey_key = db.Column(db.Integer)


class Question(db.Model):
    __tablename__ = "question"
    key = db.Column(db.Integer, primary_key=True)
    question = db.Column(db.String(128), index=True)
    used = db.Column(db.Boolean)
    optional = db.Column(db.Boolean)
    is_text = db.Column(db.Boolean)


    @property
    def answers(self):
        return Answer.query.filter(Answer.question_key == self.key).all()

    def __repr__(self):
        return "Question(key={}, question={}, answer={}, used={})".format(self.key, self.question, self.answers, self.used)

    @staticmethod
    def createFromRequest(request):
        print(request.form)
        optional = (request.form["optional"] == "true")
        is_text = (request.form["is_text"] == "true")
        question_text = request.form["question"]
        if not is_text:
            keys = sorted(request.form.keys())
            answers = [request.form[key] for key in keys if key.startswith("answer")]
        else:
            answers = []
        question = Question(question=question_text, optional=optional, is_text=is_text, used=True)
        db.session.add(question)
        db.session.commit()
        for text in answers:
            db.session.add(Answer(answer = text, question_key = question.key))
        db.session.commit()
        return question

    @staticmethod
    def updateFromRequest(request):
        print(request.form)
        optional = (request.form["optional"] == "true")
        is_text = (request.form["is_text"] == "true")
        question_text = request.form["question"]
        if not is_text:
            keys = sorted(request.form.keys())
            answers = [request.form[key] for key in keys if key.startswith("answer")]
        else:
            answers = []

        question = Question.query.filter(Question.key == int(request.form["id"][2:])).first()
        question.question = question_text
        question.optional = optional
        question.is_text = is_text
        db.session.add(question)
        db.session.commit()
        for answer in Answer.query.filter(Answer.question_key==question.key).all():
            db.session.delete(answer)
        for text in answers:
            db.session.add(Answer(answer = text, question_key = question.key))
        db.session.commit()
        return question

    def asDict(self):
        return dict(key=self.key, question=self.question, answers=[(answer.key,answer.answer) for answer in self.answers])

class Answer(db.Model):
    __tablename__ = "answer"
    key = db.Column(db.Integer, primary_key=True)
    question_key = db.Column(db.Integer, index=True)
    answer = db.Column(db.String(128))

class QuestionPool:
    @property
    def questions(self):
        return Question.query.all()
question_pool = QuestionPool()

class Survey(db.Model):
    __tablename__ = "survey"
    name = db.Column(db.String(64))
    course = db.Column(db.String(64))
    key = db.Column(db.Integer, primary_key=True)
    expired = db.Column(db.Boolean)
    confirmation = db.Column(db.Boolean)

class SurveyQuestionPair(db.Model):
    __tablename__ = "SurveyQuestionPair"
    key = db.Column(db.Integer, primary_key=True)
    question_key = db.Column(db.Integer)
    survey_key = db.Column(db.Integer, index=True)

class SurveyResponse(db.Model):
    __tablename__ = "SurveyResponse"
    key = db.Column(db.Integer, primary_key=True)
    question_key = db.Column(db.Integer, index=True)
    survey_key = db.Column(db.Integer, index=True)
    answer_key = db.Column(db.Integer)
    count = db.Column(db.Integer)
    text_answer = db.Column(db.String(512))


class Course(db.Model):
    __tablename__ = 'course'
    id = db.Column(db.Integer,index = True, primary_key = True)
    course_id = db.Column(db.String(20))

    def insert_course(self):
        for row in readfile('courses.csv'):
            db.session.add(Course(course_id = row[0] + " " + row[1]))
        db.session.commit()
        db.session.close()


class Password(db.Model):
    __tablename__ = 'password'

    zid = db.Column(db.String(3),primary_key=True)
    password = db.Column(db.String(9))
    user = db.Column(db.String(9))

    def insert_password(self):
        for row in readfile('passwords.csv'):
            db.session.add(Password(zid=row[0], password=row[1], user=row[2]))
        db.session.commit()
        db.session.close()

class Enrolment(db.Model):
    __tablename__ = 'enrolment'
    enrolment_key = db.Column(db.Integer, index=True, primary_key=True)
    zid = db.Column(db.String(3), db.ForeignKey(Password.zid))
    student = db.relationship(Password)
    course_id = db.Column(db.String(20), db.ForeignKey(Course.course_id))
    course = db.relationship(Course)

    def insert_enrolment(self):
        for row in readfile('enrolments.csv'):
            db.session.add(Enrolment(zid = row[0], course_id = row[1] + " " + row[2]))
        db.session.commit()
        db.session.close()
