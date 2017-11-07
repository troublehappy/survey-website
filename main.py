from flask import Flask, session, flash, redirect, render_template, request, url_for, jsonify
from flask_login import LoginManager,login_user, current_user, login_required, logout_user
from bokeh.io import show, output_file
from bokeh.models import ColumnDataSource
from bokeh.palettes import Spectral6
from bokeh.plotting import figure
from bokeh.transform import factor_cmap
from bokeh.embed import components
from server import app, db, login_manager
from model import User
from functools import wraps
from sqlalchemy_utils import database_exists
from config import SQLALCHEMY_DATABASE_URI
from read_write import *
from tables import *
import random

def setup_db():
    if not database_exists(SQLALCHEMY_DATABASE_URI):
        db.create_all()

        e = Enrolment()
        e.insert_enrolment()

        p = Password()
        p.insert_password()

        c = Course()
        c.insert_course()

def requires_roles(*roles):
    def wrapper(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            if get_current_user_role() not in roles:
                return render_template("error.html")
            return f(*args, **kwargs)
        return wrapped
    return wrapper

def get_current_user_role():
    return Password.query.filter(Password.zid == user_id).first().user

def completedSurvey(survey_id):
    completed = StudentCompletedSurveys.query.filter(
                    StudentCompletedSurveys.student_id == user_id,
                    StudentCompletedSurveys.survey_key == survey_id
                    ).first()
    return completed != None

def surveys_for_a_course(course):
    if get_current_user_role() == "student":
        return [(survey,completedSurvey(survey.key)) for survey in Survey.query.filter(Survey.course == course).all() if not survey.expired]
    return [survey for survey in Survey.query.filter(Survey.course == course).all()]

def all_surveys():
    return Survey.query.all()

def all_courses():
    return [course.course_id for course in Course.query.all()]

def get_current_user_enrolment():
    return [[enrolment.course_id, surveys_for_a_course(enrolment.course_id)] for enrolment in Enrolment.query.filter(Enrolment.zid == user_id).all()]


def check_password(user_id,password):
    if password == Password.query.filter(Password.zid == user_id).first().password:
        user = User(user_id)
        login_user(user)
        return True
    return False

def get_user(user_id):
    return User(user_id)

@login_manager.user_loader
def load_user(user_id):
    # get user information from db
    user = get_user(user_id)
    return user

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))

@app.route('/',methods=["GET","POST"])
def login():
    error = None
    if request.method == "POST":
        global user_id
        user_id = int(request.form["zid"])
        password = request.form["password"]
        role = Password.query.filter(Password.zid == user_id).first().user
        if check_password(user_id, password):
            if role == "admin":
                return redirect(url_for("index"))
            elif role == "staff":
                return redirect(url_for("staff_index"))
            elif role == "student":
                return redirect(url_for("student_index"))
        else:
            error = 'Invalid Credentials. Please try again.'
    return render_template("login.html", error=error)


@app.route("/index", methods=["GET","POST"])
@login_required
@requires_roles("admin")
def index():
    if request.method == "POST":
        if "ViewQuestions" in request.form:
            return redirect(url_for("view_questions"))
        elif "ViewAnswers" in request.form:
            return redirect(url_for("view_answers"))
        elif "ViewSurveys" in request.form:
            return redirect(url_for("view_all_surveys"))
    return render_template("mainindex.html")

@app.route("/api/close_survey", methods=["POST"])
@login_required
@requires_roles("admin")
def close_survey():
    survey = Survey.query.filter(Survey.key == request.form["id"]).first()
    if survey:
        survey.expired = request.form["close"] == 'true'
        db.session.add(survey)
        db.session.commit()
        return "ok"
    else:
        return "oh no", 400

@app.route("/api/create-question", methods=["POST"])
@login_required
@requires_roles("admin")
def create_new_questions():
    question = Question.createFromRequest(request)
    # print(question)
    return jsonify(question.asDict())

@app.route("/view-all-surveys", methods=["GET","POST"])
@login_required
@requires_roles("admin","staff")
def view_all_surveys():
    return render_template("viewAllSurveys.html",available_survey = all_surveys())

@app.route("/view-question", methods=["GET","POST"])
@login_required
@requires_roles("admin")
def view_questions():
    return render_template("viewQuestions.html", all_courses=all_courses(), all_questions=question_pool.questions, random=random.random())

@app.route("/api/question/delete", methods=["POST"])
@requires_roles("admin")
def delete_question():
    print(request.form)
    question = Question.query.filter(Question.key == request.form["id"]).first()
    question.used = False
    db.session.add(question)
    db.session.commit()
    return "{} is deleted\n".format(question.key)

@app.route("/api/question/undelete", methods=["POST"])
@requires_roles("admin")
def undelete_question():
    print(request.json)
    question = Question.query.filter(Question.key == request.json["id"]).first()
    question.used = True
    db.session.add(question)
    db.session.commit()
    return "{} is restored\n".format(question.key)

@app.route("/survey-link", methods=["POST"])
@login_required
@requires_roles("admin")
def generate_link():
    survey = Survey(name=request.form["name"], course=request.form["course"], expired=False, confirmation = False)
    db.session.add(survey)
    db.session.commit()
    ids = request.form["ids"]
    ids = [id[2:] for id in ids.split(",")]
    for qid in ids:
        pair = SurveyQuestionPair(question_key=int(qid), survey_key=survey.key)
        db.session.add(pair)
    db.session.commit()
    return str(survey.key)

@app.route("/api/update-survey-link", methods=["POST"])
@login_required
@requires_roles("staff")
def update_survey_link():
    survey = Survey.query.filter(Survey.key == request.form["survey_id"]).first()
    if survey:
        survey.confirmation = True
        db.session.add(survey)
        db.session.commit()
        ids = request.form["ids"]
        ids = [id[2:] for id in ids.split(",")]
        for qid in ids:
            question = Question.query.filter(Question.key == qid).first()
            if question.optional:
                pair = SurveyQuestionPair(question_key=int(qid), survey_key=survey.key)
                db.session.add(pair)
        db.session.commit()
        print("here")
        return redirect(url_for("staff_index"))
    else:
        return "oh no", 400
    return "ok"

@app.route("/staff-index", methods=["GET","POST"])
@login_required
@requires_roles("staff")
def staff_index():
    if request.method == "POST":
        if "ViewSurveys" in request.form:
            return redirect(url_for("display_survey_staff"))
        elif "ViewSurveyResults" in request.form:
            return redirect(url_for("view_questions"))
        elif "other" in request.form:
            return redirect(url_for("view_answers"))
    return render_template("staffIndex.html", available_survey = all_surveys(), enrolled_courses = get_current_user_enrolment() )

@app.route("/view-question", methods=["GET", "POST"])
@login_required
@requires_roles("staff")
def display_survey_staff():
    # print(question_pool.questions[-1])
    return render_template("viewQuestions.html", all_courses=all_courses(), all_questions=question_pool.questions, random=random.random())

@app.route("/api/confirm_survey", methods=["POST"])
@login_required
@requires_roles("staff")
def confirm_survey():
    print(request.form)
    survey = Survey.query.filter(Survey.key == request.form["id"]).first()
    if survey:
        survey.comfirmed = request.form["act"] == 'true'
        db.session.add(survey)
        db.session.commit()
        return "ok"
    else:
        return "oh no", 400

@app.route("/confirming-survey/<int:id>", methods=["GET", "POST"])
@login_required
@requires_roles("staff")
def confirming_survey(id):
    if request.method == "GET":
        all_survey_questions, _ = questions_for_survey(id)
        questions = question_pool.questions
        question_dict = {q.key:q for q in questions}
        survey = Survey.query.filter(Survey.key == id).first()
        if survey is None:
            return "Survey %s does not exist yet" % id
        pairs = SurveyQuestionPair.query.filter(SurveyQuestionPair.survey_key == id).all()
        all_questions = [question_dict[pair.question_key] for pair in pairs]
    if request.method == "POST":
        if 'confirmation' in request.form:
            survey = Survey.query.filter(Survey.key == id).first()
            survey.confirmation = True
            db.session.add(survey)
            db.session.commit()
        return redirect(url_for("staff_index"))
    return render_template("confirmingSurvey.html", name=survey.name, all_survey_questions=all_survey_questions, all_questions=question_pool.questions, survey_id=id, random=random.random())

@app.route("/student-index", methods=["GET","POST"])
@login_required
@requires_roles("student")
def student_index():
    if request.method == "POST":
        if "ViewSurveys" in request.form:
            return redirect(url_for("display_survey"))
        elif "ViewSurveyResults" in request.form:
            return redirect(url_for("view_questions"))
        elif "EnrolledCourse" in request.form:
            return redirect(url_for("display_survey"))
    return render_template("studentIndex.html", enrolled_courses = get_current_user_enrolment())

def questions_for_survey(id):
    questions = question_pool.questions
    question_dict = {q.key:q for q in questions}
    survey = Survey.query.filter(Survey.key == id).first()
    pairs = SurveyQuestionPair.query.filter(SurveyQuestionPair.survey_key == id).all()
    return [question_dict[pair.question_key] for pair in pairs], survey

@app.route("/survey/<int:id>", methods=["GET", "POST"])
@login_required
def display_survey(id):
    if request.method == "GET":
        all_questions, survey = questions_for_survey(id)
        if survey is None:
            return "Survey %s does not exist yet" % id
        completedSurvey = StudentCompletedSurveys.query.filter(
            StudentCompletedSurveys.student_id==user_id,
            StudentCompletedSurveys.survey_key==id
        ).first()
        if completedSurvey:
            return "You have already completed survey %s" % id
        if survey.expired:
            return "Survey %s has been closed" % id
    if request.method == "POST":
        for q_id, a_id in request.form.items():
            if q_id != "submit":
                questions = Question.query.filter(Question.key == q_id).first()
                if questions.is_text:
                    response = SurveyResponse.query.filter(
                        SurveyResponse.question_key==q_id,
                        SurveyResponse.survey_key==id,
                        SurveyResponse.answer_key==0,
                        SurveyResponse.text_answer==a_id
                    ).first()
                if not questions.is_text:
                    response = SurveyResponse.query.filter(
                        SurveyResponse.question_key==q_id,
                        SurveyResponse.survey_key==id,
                        SurveyResponse.answer_key==a_id,
                        SurveyResponse.text_answer==""
                    ).first()
                if response is None:
                    response = SurveyResponse(question_key=q_id, survey_key=id, answer_key=a_id, count=1)
                else:
                    response.count += 1
                db.session.add(response)
        completed = StudentCompletedSurveys(student_id=user_id, survey_key=id)
        db.session.add(completed)
        db.session.commit()
        return redirect(url_for("response_exit"))
    return render_template("viewSurveys.html", name=survey.name, all_questions=all_questions, student_id=user_id)

@app.route("/display-survey-results/<int:survey_id>")
@login_required
def display_survey_results(survey_id):
    survey = Survey.query.filter(Survey.key == survey_id).first()
    pairs = SurveyQuestionPair.query.filter(SurveyQuestionPair.survey_key == survey_id).all()
    question_keys = sorted(pair.question_key for pair in pairs)
    questions = [Question.query.filter(Question.key==q_id).first() for q_id in question_keys]
    counts = {}
    labels = {}
    text_responses = []

    for question in questions:
        q_id = question.key
        if question.is_text is True:
            responses = SurveyResponse.query.filter(SurveyResponse.survey_key==survey_id, SurveyResponse.question_key==q_id).all()
            responses = [response.answer_key for response in responses]
            text_responses.append([question.question, responses])
        else:
            answers = Answer.query.filter(Answer.question_key==q_id).all()
            counts[q_id] = {a.key:0 for a in answers}
            labels[q_id] = {a.key:a.answer for a in answers}
            responses = SurveyResponse.query.filter(
                SurveyResponse.survey_key == survey_id,
                SurveyResponse.question_key == q_id).all()
            for response in responses:
                counts[q_id][response.answer_key] = response.count

    result = []
    for q_id in sorted(counts):
        result.append([
            [label for _, label in sorted(labels[q_id].items())],
            [count for _, count in sorted(counts[q_id].items())],
        ])
    plots = [chart(q.question, *r) for q, r in zip(questions, result)]
    script, divs = components(plots)

    return render_template("response_chart.html", script=script, divs=divs, text_responses=text_responses, survey_name = survey.name)

def chart(title, labels, counts):
    p = figure(x_range=labels, plot_height=250, title=title, toolbar_location=None, tools="")
    p.vbar(x=labels, top=counts, width=0.9)
    p.y_range.start = 0
    return p


@app.route("/response-exit")
@login_required
def response_exit():
    return render_template("responseExit.html")
