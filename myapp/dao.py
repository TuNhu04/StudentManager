
from models import *
from myapp import db
import hashlib
from _datetime import datetime
from sqlalchemy import or_, func

def auth_user(username, password):
    if username and password:
        password_hash = hashlib.md5(password.encode('utf-8')).hexdigest()
        user = User.query.filter_by(username=username).first()
        if user and user.password == password_hash:
            return user

def get_user_by_id(user_id):
    return User.query.get(user_id)

def add_student(first_name,last_name,birthday,gender, address, email, phone, avatar):
    student = Student(first_name= first_name, last_name=last_name,date_of_birth=birthday, gender=gender,
                      address=address, email=email, phone=phone, avatar=avatar)
    db.session.add(student)
    db.session.commit()
    return student

def get_student_by_id(student_id):
    return Student.query.get(student_id)

def age_student(birthday):
    birthdate = datetime.strptime(birthday, "%Y-%m-%d")
    today = datetime.today()
    age = today.year - birthdate.year - ((today.month, today.day) < (birthdate.month, birthdate.day))
    return age

def load_student(page=None, class_id=None, name_student=None):
    classes = active_semester().classes
    class_ids = [cls.id for cls in classes]
    query = Student.query.join(class_student).filter(
        class_student.c.class_id.in_(class_ids))
    if class_id:
        query = Student.query.join(class_student).filter(
            class_student.c.class_id == class_id)
    if name_student:
        name_student = name_student.strip().lower()
        query = query.filter(or_(
            Student.first_name.ilike(f"%{name_student}%"),
            Student.last_name.ilike(f"%{name_student}%"),
            func.concat(Student.first_name, ' ', Student.last_name).ilike(f"%{name_student}%")
        ))
    if page:
        page_size = app.config['PAGE_SIZE']
        start = (int(page)-1)*page_size
        query = query.slice(start, start+page_size)
    return query.all()

def count_student():
    classes = active_semester().classes
    class_ids = [cls.id for cls in classes]
    total = Student.query.join(class_student).filter(
        class_student.c.class_id.in_(class_ids)).count()
    return total

def add_student_in_class(grade=None, student = None):
    semester = active_semester()
    if not semester.classes:
        new_class = create_class(grade)
        student.classes.append(new_class)
        new_class.total_student += 1
        semester.classes.append(new_class)
    else :
        classes_with_fewer_students = [
        c for c in active_semester().classes
        if c.grade == grade and c.total_student < get_rule_by_name('maxToltalStudent').value
        ]
        if not classes_with_fewer_students:
            new_class = create_class(grade)
            student.classes.append(new_class)
            new_class.total_student += 1
            semester.classes.append(new_class)
        else:
            student.classes.append(classes_with_fewer_students[0])
            classes_with_fewer_students[0].total_student +=1
    db.session.commit()

def delete_student(student):
    class_active = active_semester().classes
    classes_student = [cls for cls in student.classes if cls in class_active]
    for cls in classes_student:
        cls.total_student -= 1
        db.session.execute(
            class_student.delete().where(
                class_student.c.class_id == cls.id,
                class_student.c.student_id == student.id
            )
        )
    db.session.commit()

def get_classes_by_grade(grade=None):
    return Class.query.filter(Class.semesters.contains(active_semester()), Class.grade == grade).all()

def active_semester():
    return Semester.query.filter_by(active=True).first()

def get_grade_by_age(age):
    if age == 15:
        grade= 10
    elif age == 16:
        grade = 11
    else:
        grade =12
    return grade

def create_class(grade):
    existing_classes = get_classes_by_grade(grade=grade)
    if grade == 10:
        name = f"{grade}{chr(65)}{len(existing_classes)+1}"
    elif grade == 11:
        name = f"{grade}{chr(66)}{len(existing_classes)+1}"
    else:
        name = f"{grade}{chr(67)}{len(existing_classes)+1}"
    new_class = Class(grade=grade,name=name)
    db.session.add(new_class)
    db.session.commit()
    return new_class

def load_class(page=None):
    classes = active_semester().classes
    class_ids = [cls.id for cls in classes]
    query = Class.query.filter(Class.id.in_(class_ids))
    if page:
        page_size = app.config['PAGE_SIZE']
        start = (int(page)-1)*page_size
        query = query.slice(start, start+page_size)
    return query.all()

def get_total_student(class_id):
    cls = Class.query.get(class_id)
    return cls.total_student

def count_class():
    classes = active_semester().classes
    class_ids = [cls.id for cls in classes]
    query = Class.query.filter(Class.id.in_(class_ids))
    return query.count()

def name_class_student(student=None):
    semester_id = active_semester().id
    for cls in student.classes:
        if any(semester.id == semester_id for semester in cls.semesters):
            return cls.name #lấy tên lớp cho danh sách học sinh

def load_student_no_class():
    student_ids =[ s.id for s in load_student()]
    query = (Student.query.outerjoin(class_student, class_student.c.student_id == Student.id)
             .filter(or_( class_student.c.student_id.is_(None),
                        ~class_student.c.student_id.in_(student_ids)))
             .filter(Student.graduated == False))
    return query.all()

def get_class_by_id(class_id):
    return Class.query.get(class_id)

def add_student_class(class_id, student_id):
    student = get_student_by_id(student_id)
    cls = get_class_by_id(class_id)
    student.classes.append(cls)
    cls.total_student +=1
    db.session.commit()

def load_subject():
    return Subject.query.all()

def get_teacher_by_subject(subject_id):
    teachers = Teacher.query.join(SubjectDetail).filter(SubjectDetail.subject_id == subject_id).all()
    teacher_ids = [teacher.id for teacher in teachers]
    user = User.query.filter(User.id.in_(teacher_ids))
    return user.all()

def create_transcript(subject_id,teacher_id,class_id):
    subject_detail = SubjectDetail.query.filter(SubjectDetail.subject_id==subject_id,
                                                SubjectDetail.teacher_id==teacher_id).first()
    if subject_detail:
        transcript = Transcript(semester_id=active_semester().id, class_id = class_id, subject_detail_id=subject_detail.id)
        db.session.add(transcript)
        db.session.commit()

def get_subject_by_id(subject_id):
    return Subject.query.get(subject_id)

def get_subject_detail(subject_id=None,teacher_id=None,subject_detail=None):
    if subject_detail:
        return SubjectDetail.query.get(subject_detail)
    if subject_id and teacher_id:
        return SubjectDetail.query.filter(SubjectDetail.subject_id==subject_id,
                                      SubjectDetail.teacher_id==teacher_id).first()

def get_subject_of_teacher(teacher_id):
    return Subject.query.join(SubjectDetail).filter(SubjectDetail.subject_id==Subject.id,
                                                    SubjectDetail.teacher_id==teacher_id).all()
def get_class_by_subjectdetail(teacher_id, subject_id):
    subject_detail = get_subject_detail(subject_id,teacher_id)
    if subject_detail:
        transcript = Transcript.query.filter(Transcript.subject_detail_id == subject_detail.id,
                                             Transcript.semester_id==active_semester().id).all()
        cls_ids = [t.class_id for t in transcript]
        return Class.query.filter(Class.id.in_(cls_ids))


def get_filtered_subjects(class_id):
    subject_has_transcript_query = db.session.query(Subject.id).join(SubjectDetail) \
        .join(Transcript) \
        .filter(Transcript.semester_id == active_semester().id, Transcript.class_id==class_id).subquery()
    unclassified_subjects = db.session.query(Subject).filter(Subject.id.not_in(subject_has_transcript_query))
    return unclassified_subjects.all()

def get_transcript(class_id=None,subject_detail_id=None, transcript_id=None, semester_id =None):
    if transcript_id:
        return Transcript.query.get(transcript_id)
    if class_id and semester_id:
        return Transcript.query.filter(Transcript.class_id == class_id,
                                       Transcript.semester_id==semester_id).all()
    if class_id and subject_detail_id:
        return Transcript.query.filter(Transcript.subject_detail_id == subject_detail_id,
                                   Transcript.class_id == class_id,
                                   Transcript.semester_id==active_semester().id).first()
def add_column(transcript_id,type_score):
    msg = 'Đã quá số cột quy định'
    transcript = get_transcript(transcript_id=transcript_id)
    if type_score == 1 and transcript.number15Col < get_rule_by_name('maxCot15P').value:
        transcript.number15Col +=1
        msg = 'Thêm thành công'
    if type_score == 2 and transcript.number1Col < get_rule_by_name('maxCot1T').value:
        transcript.number1Col +=1
        msg = 'Thêm thành công'
    db.session.commit()
    return msg

def save_score_15p(score_15p,student_id,transcript_id):
    for diem in score_15p:
        existing_score = Score.query.filter_by(
            student_id=student_id,
            transcript_id=transcript_id,
            type='diem-15-phut',
            number_Col= diem['lan']
        ).first()
        if existing_score:
            existing_score.value = diem['value']
        else:
            new_score = Score(
                student_id=student_id,
                transcript_id=transcript_id,
                value=diem['value'],
                type='diem-15-phut',
                number_Col= diem['lan']
            )
            db.session.add(new_score)
    db.session.commit()

def save_score_1t(score_1t,student_id,transcript_id):
    for diem in score_1t:
        existing_score = Score.query.filter_by(
            student_id=student_id,
            transcript_id=transcript_id,
            type='diem-1-tiet',
            number_Col= diem['lan']
        ).first()
        if existing_score:
            existing_score.value = diem['value']
        else:
            score = Score(
                student_id=student_id,
                transcript_id=transcript_id,
                value=diem['value'],
                type='diem-1-tiet',
                number_Col= diem['lan']
            )
            db.session.add(score)
    db.session.commit()

def save_score_ck(score_ck,student_id,transcript_id):
    existing_score = Score.query.filter_by(student_id=student_id,
                    transcript_id=transcript_id,type='diem-thi',number_Col= 1).first()
    if existing_score:
        existing_score.value = score_ck
    else:
        new_score = Score( student_id=student_id,transcript_id=transcript_id, value= score_ck,
                           type='diem-thi',number_Col= 1)
        db.session.add(new_score)
    db.session.commit()

def get_scores_by_transcript_id(transcript_id=None):
    scores = Score.query.filter(Score.transcript_id==transcript_id).all()
    student_scores = {}
    for score in scores:
        student_id = score.student_id
        if student_id not in student_scores:
            student_scores[student_id] = {
                'diem_15_phut': [],
                'diem_1_tiet': [],
                'diem_thi': None
            }
        if score.type == 'diem-15-phut':
            student_scores[student_id]['diem_15_phut'].append({
                'lan': score.number_Col,
                'value': score.value
            })
        elif score.type == 'diem-1-tiet':
            student_scores[student_id]['diem_1_tiet'].append({
                'lan': score.number_Col,
                'value': score.value
            })
        elif score.type == 'diem-thi':
            student_scores[student_id]['diem_thi'] = score.value
    return student_scores

def get_rule_by_name(name):
    return Rule.query.filter(Rule.name==name).first()

def avg_score_semester(student_id,transcript_id):
    transcript = get_transcript(transcript_id=transcript_id)
    number15Col = transcript.number15Col
    number1Col = transcript.number1Col
    score_15p = Score.query.filter(Score.student_id==student_id,Score.transcript_id==transcript_id,
                                   Score.type =='diem-15-phut').all()
    score_1t = Score.query.filter(Score.student_id==student_id,Score.transcript_id==transcript_id,
                                   Score.type =='diem-1-tiet').all()
    score_ck = Score.query.filter(Score.student_id==student_id,Score.transcript_id==transcript_id,
                                   Score.type =='diem-thi').first()
    if score_15p:
        sum_15p = sum([score.value for score in score_15p])
    else:
        sum_15p = 0
    if score_1t:
        sum_1t = sum([score.value for score in score_1t])
    else:
        sum_1t = 0
    ck = score_ck.value if score_ck else 0
    final_avg = (sum_15p + sum_1t*2 + ck*3 )/(number15Col+number1Col*2+3)
    return round(final_avg,1)

def final_score_by_semester(class_id,subject_id,teacher_id,year_id):
    academicyear = AcademicYear.query.get(year_id)
    if academicyear:
        semesters = academicyear.semesters
    semester_scores = []
    students = Student.query.join(class_student).filter(
        class_student.c.class_id == class_id ).all()
    for student in students:
        subject_detail = get_subject_detail(subject_id=subject_id,teacher_id=teacher_id)
        transcript_hk1 = Transcript.query.filter_by( class_id=class_id, subject_detail_id=subject_detail.id,
                                                    semester_id=semesters[0].id).first()
        transcript_hk2 = Transcript.query.filter_by(class_id=class_id, subject_detail_id=subject_detail.id,
                                                    semester_id=semesters[1].id).first()
        hk1_score = avg_score_semester(student.id, transcript_hk1.id) if transcript_hk1 else 0
        hk2_score = avg_score_semester(student.id, transcript_hk2.id) if transcript_hk2 else 0
        semester_scores.append({
            'first_name': student.first_name,
            'last_name': student.last_name,
            'hk1_score': hk1_score,
            'hk2_score': hk2_score
        })
    return semester_scores

def load_academicyear():
    academicyears = AcademicYear.query.all()
    return [ year for year in academicyears if len(year.semesters) == 2]

def class_of_teacher(teacher_id):
    subject_detail = SubjectDetail.query.filter(SubjectDetail.teacher_id==teacher_id)
    sd_ids = [s.id for s in subject_detail]
    classes = Class.query.join(Transcript).filter(Transcript.subject_detail_id.in_(sd_ids))
    return classes.all()

def count_teacher():
    return User.query.filter(User.role == Role.TEACHER).count()

def count_grade(grade):
    return Class.query.filter(Class.grade==grade).count()

def get_academicyear(academicyear_id=None,academicyear_name=None):
    if academicyear_id:
        return AcademicYear.query.get(academicyear_id)
    if academicyear_name:
        return AcademicYear.query.filter(AcademicYear.name==academicyear_name).first()

def end_semester():
    semester = active_semester()
    classes = semester.classes
    if semester.name == '1':
        semester.active = False
        new_semester = Semester(name='2', active=True, academic_year_id=semester.academic_year_id)
        db.session.add(new_semester)
        db.session.flush()
        for c in classes:
            c.semesters.append(new_semester)
            db.session.commit()
            upgrade_transcript(c.id)
        db.session.commit()
    else:
        academicyear = get_academicyear(academicyear_id=semester.academic_year_id)
        start_year, end_year = map(int,academicyear.name.split('-'))
        next_year_name = f"{start_year + 1}-{end_year + 1}"
        new_academic_year = AcademicYear(name=next_year_name)
        db.session.add(new_academic_year)
        db.session.flush()
        semester.active = False
        new_semester = Semester(name='1', active=True, academic_year_id = new_academic_year.id)
        db.session.add(new_semester)
        db.session.commit()
        for c in classes:
            if c.grade < 12:
                new_grade = c.grade + 1
                new_class_name = f"{new_grade}{c.name[2:]}"  # Giữ nguyên phần ký tự sau số lớp
                new_class = Class(grade=new_grade, name=new_class_name)
                db.session.add(new_class)
                new_class.semesters.append(active_semester())
                for student in c.students:
                    upgrade_class(student_id=student.id,class_id=c.id,new_class_id=new_class.id)
            else:
                for student in c.students:
                    upgrade_class(student_id=student.id, class_id=c.id)

def upgrade_class(student_id,class_id,new_class_id=None):
    cls = get_class_by_id(class_id=class_id)
    semesters = cls.semesters
    student = get_student_by_id(student_id)
    transcripts_hk1 = get_transcript(class_id=cls.id, semester_id = semesters[0].id)
    transcripts_hk2 = get_transcript(class_id=cls.id, semester_id=semesters[1].id)
    avg_score_hk1 = 0
    avg_score_hk2 = 0
    for t in transcripts_hk1:
        avg_score_hk1 += avg_score_semester(student_id,t.id)
    for t in transcripts_hk2:
        avg_score_hk2 += avg_score_semester(student_id, t.id)
    avg_score_hk1 /= Subject.query.count()
    avg_score_hk2 /= Subject.query.count()
    total_score = round((avg_score_hk1 + avg_score_hk2) /2)
    if total_score > 3.5:
        if new_class_id:
            new_class = get_class_by_id(new_class_id)
            student.classes.append(new_class)
            new_class.total_student+=1
        else:
            student.graduated=True
    db.session.commit()

def upgrade_transcript(class_id):
    semester = active_semester()
    cls = get_class_by_id(class_id)
    transcripts = cls.subject_details
    for t in transcripts:
        new_transcript = Transcript(semester_id=semester.id,class_id=class_id,subject_detail_id=t.subject_detail_id)
        db.session.add(new_transcript)
    db.session.commit()

