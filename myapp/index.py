from models import Role
from flask import render_template, request, jsonify, redirect, url_for, flash
from myapp import app, dao, login, admin
from flask_login import login_user, logout_user, current_user
import cloudinary.uploader
import math

@app.route("/", methods=['get','post'])
def login_account():
    err_msg=''
    if request.method.__eq__('POST'):
        username = request.form.get('username')
        password = request.form.get('password')
        user = dao.auth_user(username,password)
        if user:
            login_user(user)
            role = user.role
            if role == Role.EMPLOYEE:
                return redirect(url_for('user_employee'))
            elif role == Role.TEACHER:
                return redirect(url_for('user_teacher'))
            else:
                return redirect(url_for('admin.index'))
        else:
            err_msg = "Tài khoản hoặc mật khẩu không đúng!"
    return render_template('index.html',err_msg=err_msg)

@app.route('/admin_login', methods =['POST'])
def signin_admin():
    username = request.form.get('username')
    password = request.form.get('password')
    user = dao.auth_user(username, password)
    if user:
        login_user(user)
        if user.role == Role.ADMIN:
            return redirect(url_for('admin.index'))
        else:
            return redirect(url_for('index'))
    else:
        return "Tài khoản hoặc mật khẩu không đúng!"

@login.user_loader
def load_user(user_id):
    return dao.get_user_by_id(user_id)

@app.route('/logout')
def logout_account():
    logout_user()
    return redirect(url_for('login_account'))

@app.route("/nhanvien")
def user_employee():
    count_student = dao.count_student()
    count_teacher = dao.count_teacher()
    count_grade10 = dao.count_grade(10)
    count_grade11 = dao.count_grade(11)
    count_grade12 = dao.count_grade(12)
    semester = dao.active_semester()
    year = dao.get_academicyear(academicyear_id=semester.academic_year_id).name
    return render_template('employee.html', count_teacher=count_teacher, count_student=count_student,
                           semester=semester.name, year=year, count_grade10=count_grade10, count_grade11=count_grade11,
                           count_grade12=count_grade12)

@app.route("/danhsachhocsinh/")
def load_student():
    search = request.args.get("search")
    page = request.args.get("page")
    if not page:
        page = 1
    students = dao.load_student(page=page,name_student=search)
    for index, student in enumerate(students, start=((int(page)-1)*app.config['PAGE_SIZE'])+1):
        student.name_class = dao.name_class_student(student)
        student.stt = index
    total = dao.count_student()
    return render_template('danhsachhocsinh.html', students=students, pages=math.ceil(total/app.config['PAGE_SIZE']))

@app.route("/tiepnhanhocsinh", methods=['get', 'post'])
def add_student():
    err_msg = None
    success_msg = None
    if request.method.__eq__('POST'):
        first_name = request.form.get("f_name")
        last_name = request.form.get("l_name")
        birthday = request.form.get("brthd")
        gender = request.form.get("gender")
        address = request.form.get("address")
        email = request.form.get("email")
        phone = request.form.get("phone")
        avatar = request.files.get("avatar")
        age = dao.age_student(birthday)
        if len(phone) != 10:
            err_msg = 'Số điện thoại không đúng. Vui lòng nhập lại!'
            return render_template('hocsinh.html', err_msg=err_msg)
        if age >= dao.get_rule_by_name('minAge').value and age <= dao.get_rule_by_name('maxAge').value:
            if all([first_name,last_name, birthday, gender, address, email, phone, avatar ]):
                res = cloudinary.uploader.upload(avatar)
                avatar_path = res['secure_url']
                success_msg = "Thêm học sinh thành công"
                student = dao.add_student(first_name= first_name.strip(), last_name=last_name.strip(), birthday=birthday, gender=gender,
                              address=address, email=email, phone=phone, avatar=avatar_path)
                grade = dao.get_grade_by_age(age=age)
                dao.add_student_in_class(grade=grade, student=student)
            else:
                err_msg = "Vui lòng nhập đầy đủ thông tin"
        else:
            err_msg = "Tuổi không đúng quy định"
    return render_template('hocsinh.html', err_msg = err_msg , success_msg=success_msg)

@app.route("/lop")
def load_class():
    page = request.args.get("page")
    classes = dao.load_class(page)
    if not page:
        page =1
    for index, c in enumerate(classes, start=((int(page)-1)*app.config['PAGE_SIZE'])+1):
        c.stt = index
    total = dao.count_class()
    return render_template('lop.html', classes=classes, pages=math.ceil(total/app.config['PAGE_SIZE']))

@app.route("/dieuchinhlop/<int:class_id>", methods=['get', 'post'])
def load_classsetting(class_id):
    search_name = request.args.get("search")
    page = request.args.get("page")
    classes = dao.load_class()
    if not page:
        page = 1
    students = dao.load_student(page=page,class_id=class_id,name_student=search_name)
    total = dao.get_total_student(class_id)
    cls = dao.get_class_by_id(class_id)
    for index, student in enumerate(students, start=((int(page)-1)*app.config['PAGE_SIZE'])+1):
        student.stt = index
    return render_template('dieuchinhlop.html', cls=cls, classes=classes,
                   search_name=search_name,students=students, pages=math.ceil(total/app.config['PAGE_SIZE']))

@app.route('/api/delete_student/<int:student_id>', methods=['DELETE'])
def delete_student(student_id):
        student = dao.get_student_by_id(student_id)
        if student:
            dao.delete_student(student)
            return jsonify({'success': True})

@app.route('/themhocsinh/<int:class_id>')
def student_no_class(class_id):
    if dao.get_total_student(class_id) < dao.get_rule_by_name('maxToltalStudent').value:
        students = dao.load_student_no_class()
        for index, student in enumerate(students, start=1):
            student.stt = index
    else:
        students = []
    return render_template('themhocsinh.html', students=students,
                           class_id=class_id)

@app.route('/api/add-student', methods=['POST'])
def add_student_to_class():
    data = request.json
    student_id = data.get('student_id')
    class_id = data.get('class_id')
    if student_id and class_id and dao.get_total_student(class_id)<=3:
        dao.add_student_class(class_id,student_id)
        return jsonify({'content': 'Thêm học sinh thành công'})
    else:
        return jsonify({'content': 'Lớp đã đủ sĩ số'})

@app.route('/chitietmon/<int:class_id>',  methods=['GET'])
def arrange_schedule(class_id):
    subject_id = request.args.get('subject_id')
    teacher_id = request.args.get('teacher_id')
    cls = dao.get_class_by_id(class_id)
    if teacher_id:
        dao.create_transcript(subject_id, teacher_id, class_id)
        return redirect('/chitietmon/'+ str(class_id))
    teachers = dao.get_teacher_by_subject(subject_id)
    filtered_subjects = dao.get_filtered_subjects(class_id)
    return render_template('lichday.html',filtered_subjects=filtered_subjects ,
                        teachers=teachers,subject_id=subject_id, cls=cls)

@app.route('/giaovien')
def user_teacher():
    count_student = dao.count_student()
    count_teacher = dao.count_teacher()
    count_grade10 = dao.count_grade(10)
    count_grade11 = dao.count_grade(11)
    count_grade12 = dao.count_grade(12)
    semester = dao.active_semester()
    year = dao.get_academicyear(academicyear_id=semester.academic_year_id).name
    return render_template('giaovien.html', count_teacher=count_teacher,count_student=count_student,
                           semester=semester.name,year=year,count_grade10=count_grade10,count_grade11=count_grade11,count_grade12=count_grade12)

@app.route('/diem/', methods=['get', 'post'])
def load_score():
    subject_id = request.args.get('subject')
    if subject_id:
        classes = dao.get_class_by_subjectdetail(current_user.id, subject_id)
    else:
        classes =[]
    subjects = dao.get_subject_of_teacher(current_user.id)
    return render_template('diem.html', subjects=subjects, classes=classes,
                           subject_id=subject_id)

@app.route('/nhapdiem/<int:subject_id>',  methods=['GET'])
def input_score(subject_id):
    search = request.args.get('search')
    class_id = request.args.get('class_id')
    subject_detail_id = dao.get_subject_detail(subject_id=subject_id,teacher_id=current_user.id).id
    transcript = dao.get_transcript(class_id=class_id,subject_detail_id=subject_detail_id)
    students = dao.load_student(class_id=class_id,name_student=search)
    for index, student in enumerate(students, start= 1):
        student.stt = index
    cls = dao.get_class_by_id(class_id)
    subject = dao.get_subject_by_id(subject_id)
    if transcript:
        scores = dao.get_scores_by_transcript_id(transcript.id)
    else:
        scores = {}
    return render_template('nhapdiem.html', transcript=transcript, students=students,
                           scores=scores,subject=subject,cls=cls)

@app.route('/api/save-score', methods=['POST'])
def save_score():
    data = request.json
    transcript_id = data.get('transcript_id')
    scores = data.get('scores')
    if not transcript_id or not scores:
        return jsonify({'content': 'Dữ liệu không hợp lệ'}), 400
    for score in scores:
        student_id = score['student_id']
        score_15p = score['diem_15_phut']
        score_1t = score['diem_1_tiet']
        score_ck = score['diem_thi']
        if score_15p:
            dao.save_score_15p(score_15p, student_id, transcript_id)
        if score_1t:
            dao.save_score_1t(score_1t, student_id, transcript_id)
        if score_ck:
            dao.save_score_ck(score_ck, student_id, transcript_id)
    return jsonify({'content': 'Lưu điểm thành công'})

@app.route('/api/add-column', methods=['POST'])
def add_column():
    transcript_id = request.json.get('transcript_id')
    type_score = request.json.get('type_score')
    msg = dao.add_column(transcript_id,type_score)
    return jsonify({'content': msg})

@app.route("/xuatdiem", methods=['GET'])
def output_score():
    class_id = request.args.get('class')
    subject_id = request.args.get('subject')
    year_id = request.args.get('year')
    classes = dao.class_of_teacher(current_user.id)
    subjects = dao.get_subject_of_teacher(current_user.id)
    academicyears = dao.load_academicyear()
    semester_scores = dao.final_score_by_semester(class_id=class_id, subject_id=subject_id,teacher_id=current_user.id ,year_id=year_id)
    return render_template('xuatdiem.html', semester_scores=semester_scores, subjects=subjects,
                           year_id=year_id,subject_id=subject_id,class_id=class_id,academicyears=academicyears, classes=classes)

@app.route('/end_semester_action', methods=['POST'])
def end_semester_action():
    if current_user.role != Role.ADMIN:
        flash('Bạn không có quyền truy cập tính năng này.', 'danger')
        return redirect(url_for('admin.index'))
    try:
        dao.end_semester()  # Gọi hàm kết thúc học kỳ
        flash('Học kỳ đã kết thúc thành công!', 'success')
    except Exception as e:
        flash(f'Lỗi: {str(e)}', 'danger')
    return redirect(url_for('admin.index'))


if __name__ == "__main__":
    with app.app_context():
        app.run(debug=True)