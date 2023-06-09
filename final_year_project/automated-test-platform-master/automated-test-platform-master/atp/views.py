

import os
import click
import flask
from datetime import datetime
from flask import render_template, request

from werkzeug.utils import secure_filename
from werkzeug.datastructures import  FileStorage
from atp import app

from atp.subjective_question import generate_subj_question
from atp.cosine_similarity import evaluate_subj_answer
from atp.util import generate_trivia, get_obj_question, get_sbj_question
from atp.util import relative_ranking, back_up_data

import pandas as pd
import numpy as np


global_name_list = list()
global_answer_list = list()
global_test_id = list()
global_name_list.clear()
global_answer_list.clear()
global_test_id.clear()
global_test_id.clear()

@app.route('/')
@app.route('/home')
def home():
    ''' Renders the home page '''
    return render_template(
        "index.html",
        date=datetime.now().day,
        month=datetime.now().month,
        year=datetime.now().year
        )


@app.route("/form", methods=['GET', 'POST'])
def form():
    ''' prompt for user to start procedure of test '''
    global_name_list.clear()
    user_name = request.form["username"]
    usn = request.form["usn"]
    semester = request.form["semester"]
    if user_name == "":
        user_name = "Admin"
    
    global_name_list.append(user_name)
    global_name_list.append(usn)
    global_name_list.append(semester)

    return render_template(
        "form.html",
        username=user_name,
        usn=usn,
        semester=semester
        )


@app.route("/generate_test", methods=['GET', 'POST'])
def generate_test():
    # get subject id
    subject_id = request.form["subject_id"]
    filename = ""
    if subject_id == "1":
        global_name_list.append("Software Testing")
        filename = str(os.getcwd()) + r"/final_year_project/automated-test-platform-master/automated-test-platform-master/sample_test_data/software-testing.txt" 
        print(filename)
    elif subject_id == "2":
        global_name_list.append("DBMS")
        filename = str(os.getcwd()) + r"/final_year_project/automated-test-platform-master/automated-test-platform-master/sample_test_data/dbms.txt"
    elif subject_id == "3":
        global_name_list.append("ML")
        filename = str(os.getcwd()) + r"/final_year_project/automated-test-platform-master/automated-test-platform-master/sample_test_data/ml.txt"
    else:
        # file containing data to generate test
        file = request.files["file"]
        filename = secure_filename(file.filename)
        file.save(secure_filename(file.filename))
        global_name_list.append("Sample Test")
    
    # get test type id
    test_id = request.form["test_id"]
    global_test_id.append(test_id)

    if test_id == "1":
        # generate word/phrase question
        que_ans_pair = generate_trivia(filename)
        # get generated question and answer at random
        question_list, answer_list = get_obj_question(que_ans_pair)
        for indi_ans in answer_list:
            global_answer_list.append(indi_ans)

        return render_template(
        "give_test.html",
        username=global_name_list[0],
        usn=global_name_list[1],
        semester=global_name_list[2],
        testname=global_name_list[3],
        question1=question_list[0],
        question2=question_list[1],
        question3=question_list[2]
        )
    else:
        # generate subjective question
        que_ans_pair = generate_subj_question(filename)
        # get one of the generated question and answer at random
        question_list, answer_list = get_sbj_question(que_ans_pair)
        for indi_ans in answer_list:
            global_answer_list.append(indi_ans)

        return render_template(
        "give_test_2.html",
        username=global_name_list[0],
        usn=global_name_list[1],
        semester=global_name_list[2],
        testname=global_name_list[3],
        question1=question_list[0],
        question2=question_list[1]
        )
    


@ app.route("/output", methods=["GET", "POST"])
def output():
    # give result based on the test taken by the user
    user_ans = list()
    if global_test_id[0] == "1":
        # get objective test user responses
        temp = request.form["answer1"]
        temp = str(temp).strip(" ")
        user_ans.append(temp.upper())

        temp = request.form["answer2"]
        temp = str(temp).strip(" ")
        user_ans.append(temp.upper())

        temp = request.form["answer3"]
        temp = str(temp).strip(" ")
        user_ans.append(temp.upper())
    else:
        # subjective test user responses
        temp = request.form["answer1"]
        temp = str(temp).strip(" ")
        user_ans.append(temp.upper())

        temp = request.form["answer2"]
        temp = str(temp).strip(" ")
        user_ans.append(temp.upper())

    # get the default answer for the question
    default_ans = list()
    for x in global_answer_list:
        x = str(x)
        x = x.strip(" ")
        x = x.upper()
        default_ans.append(x)
    
    username = global_name_list[0]
    usn = global_name_list[1]
    semester = global_name_list[2]
    subjectname = global_name_list[3]
    
    # evaluate the user repsonse
    total_score = 0
    flag = ""
    if global_test_id[0] == "1":
        flag = "1"
        # evaluate objective answer
        for i in range(len(user_ans)):
            if user_ans[i] == default_ans[i]:
                total_score += 100
        total_score /= 3
        total_score = round(total_score, 3)
        # back up the user details and score for rank analysis
        status = "Score Not Saved!"
        if back_up_data(username, usn, semester, subjectname, total_score, "1") == True:
            status = "Score Saved!"
    elif global_test_id[0] == "2":
        flag = "2"
        # evaluate subjective answer
        for i in range(len(default_ans)):
            total_score += evaluate_subj_answer(default_ans[i], user_ans[i])
        total_score /= 2
        total_score = round(total_score, 3)
        # back up the user details and score for rank analysis
        status = "Score Not Saved!"
        if back_up_data(username, usn, semester , subjectname, total_score, "2") == True:
            status = "Score Saved!"

    max_score, mean_score, min_score = relative_ranking(subjectname, flag)

    # clear the global variables for the next instance
    
    user_ans.clear()
    default_ans.clear()

    return render_template(
        "output.html",
        show_score=total_score,
        username=username,
        usn=usn,
        semester=semester,
        subjectname=subjectname,
        status=status,
        max_score=max_score,
        mean_score=mean_score,
        min_score=min_score
    )
# end of the application
