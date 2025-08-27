
from sqlalchemy import Column, Integer, String, Boolean, Float, CHAR, ForeignKey, DATE, Enum as SQLAlchemyEnum
from sqlalchemy.orm import relationship, backref
from enum import Enum
from flask_login import UserMixin
import hashlib
from myapp import app, db

class Role(Enum):
    ADMIN = 1
    TEACHER = 2
    EMPLOYEE = 3

class User(db.Model, UserMixin):
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100))
    username = Column(String(50), unique=True, nullable=False)
    password = Column(String(50), nullable=False)
    avatar = Column(String(200), default="https://res.cloudinary.com/dy1unykph/image/upload/v1729842193/iPhone_15_Pro_Natural_1_ltf9vr.webp")
    active = Column(Boolean, default=True)
    role = Column(SQLAlchemyEnum(Role), nullable=False)
    teacher = relationship('Teacher', back_populates='user', uselist=False)

class Teacher(db.Model):
    id = Column(Integer, ForeignKey(User.id), primary_key=True)
    level = Column(String(50))
    user = relationship(User, back_populates='teacher')
    subjects = relationship('SubjectDetail',backref='teachers')

class Student(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True)
    first_name = Column(String(100))
    last_name = Column(String(20))
    date_of_birth = Column(DATE)
    gender = Column(String(5))
    address = Column(String(300))
    phone = Column(CHAR(10))
    email = Column(String(100))
    avatar = Column(String(200), default="https://res.cloudinary.com/dz03d8gcs/image/upload/v1733493095/18148_l8fyrd.png")
    graduated = Column(Boolean, default=False)
    classes = relationship('Class', secondary= 'class_student', backref=backref('students',lazy=True), lazy=True)
    scores = relationship('Score', backref='student', lazy=True)

class Class(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100),nullable=False)
    grade =  Column(Integer, nullable=False)
    total_student = Column(Integer, default=0)
    subject_details = relationship('Transcript', backref='class')

class AcademicYear(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100))
    semesters = relationship('Semester', backref='academicyear', lazy=True)

class Semester(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100))
    active = Column(Boolean, default=True)
    academic_year_id = Column(Integer, ForeignKey(AcademicYear.id), nullable=False)
    classes = relationship(Class, secondary= 'class_semester', backref=backref('semesters',lazy=True), lazy=True)
    transcripts = relationship('Transcript', backref='semester', lazy=True)

class Subject(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), unique=True, nullable=False)
    teachers = relationship('SubjectDetail',backref='subject')

class SubjectDetail(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True)
    classes = relationship('Transcript',backref='subject_detail')
    subject_id = Column(Integer, ForeignKey(Subject.id), nullable=False)
    teacher_id = Column(Integer, ForeignKey(Teacher.id), nullable=False)

class Transcript(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True)
    number15Col = Column(Integer,default=1)
    number1Col = Column(Integer,default=1)
    semester_id = Column(Integer, ForeignKey(Semester.id), nullable=False)
    class_id = Column(Integer, ForeignKey(Class.id), nullable=False)
    subject_detail_id = Column(Integer, ForeignKey(SubjectDetail.id), nullable=False)
    scores = relationship('Score', backref='transcript', lazy=True)

class Score(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True)
    value = Column(Float,default=0.0)
    type = Column(String(50),nullable=False)
    number_Col = Column(Integer, nullable=False)
    transcript_id = Column(Integer, ForeignKey(Transcript.id), nullable=False)
    student_id = Column(Integer, ForeignKey(Student.id), nullable=False)

class Rule(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100))
    value = Column(Float, default=0.0)
    description = Column(String(500), default='')

class_semester = db.Table(
    'class_semester',
    Column('class_id', Integer, ForeignKey(Class.id), primary_key=True),
    Column('semester_id', Integer, ForeignKey(Semester.id), primary_key=True)
)

class_student = db.Table(
    'class_student',
    Column('class_id', Integer, ForeignKey(Class.id), primary_key=True),
    Column('student_id', Integer, ForeignKey(Student.id), primary_key=True)
)

if __name__ == "__main__":
    with app.app_context():
        db.drop_all()
        db.create_all()
        s1 = Subject(name="Ngữ văn")
        s2 = Subject(name="Toán")
        s3 = Subject(name="Ngoại ngữ")
        db.session.add_all([s1,s2,s3])
        year = AcademicYear(name='2024-2025')
        hk1 = Semester(name='1',active=True,academic_year_id=1)
        userT1 = User(name='Nguyễn Thị Ánh', username='teacher1',
                  password=str(hashlib.md5('123456'.encode('utf-8')).hexdigest()), role=Role.TEACHER)
        userT2 = User(name='Huỳnh An', username='teacher2',
                  password=str(hashlib.md5('123456'.encode('utf-8')).hexdigest()), role=Role.TEACHER)
        userNV1 = User(name='Nguyễn Hữu Tài', username='employee1',
                  password=str(hashlib.md5('123456'.encode('utf-8')).hexdigest()), role=Role.EMPLOYEE)
        userAdmin = User(name='Phạm Ngọc Ánh Nguyệt', username='admin1',
                  password=str(hashlib.md5('123456'.encode('utf-8')).hexdigest()), role=Role.ADMIN)
        db.session.add_all([year,hk1,userT1,userT2,userNV1,userAdmin])
        db.session.flush()
        t1 = Teacher(id=userT1.id, level='Thạc sĩ')
        t2 = Teacher(id=userT2.id, level='Thạc sĩ')
        db.session.add_all([t1,t2])
        db.session.flush()
        sd1 = SubjectDetail(subject_id=s1.id,teacher_id=t1.id)
        sd2 = SubjectDetail(subject_id=s2.id, teacher_id=t2.id)
        sd3 = SubjectDetail(subject_id=s3.id, teacher_id=t1.id)
        db.session.add_all([sd1,sd2,sd3])
        r1 = Rule(name='minAge', value=15, description = 'Tuổi nhỏ nhất của học sinh')
        r2 = Rule(name='maxAge', value=20, description = 'Tuổi lớn nhất của học sinh')
        r3 = Rule(name='maxCot15P', value=5, description = 'Số cột điểm 15 phút tối đa của mỗi môn học')
        r4 = Rule(name='maxCot1T', value=3, description = 'Số cột điểm 1 tiết tối đa của mỗi môn học')
        r5 = Rule(name='maxToltalStudent', value=40, description='Số lượng tối đa của mỗi lớp')
        db.session.add_all([r1,r2,r3,r4,r5])
        st1 = Student(first_name="Nguyễn Thanh", last_name="Tùng", date_of_birth="2008-05-15", gender="Nam",
                address="Hà Nội", phone="0123456789", email="vanan@gmail.com")
        st2 = Student(first_name="Trần Ngọc", last_name="Bích", date_of_birth="2008-08-20", gender="Nu",
                address="Hồ Chí Minh", phone="0987654321", email="thibich@gmail.com")
        st3 = Student(first_name="Phạm Bảo", last_name="Khang", date_of_birth="2007-05-04", gender="Nam",
                address="Đà Nẵng", phone="0912345678", email="khang@gmail.com")
        cls1 = Class(name="11A1", grade=11)
        cls2 = Class(name="12A1", grade=12)
        db.session.add_all([st1,st2,st3,cls1,cls2])
        db.session.flush()
        hk1.classes.append(cls1)
        hk1.classes.append(cls2)
        # lớp cls1 có 2 học sinh: st1 và st2
        st1.classes.append(cls1)
        st2.classes.append(cls1)
        cls1.total_student +=2
        # lớp cls2 có 1 học sinh: st3
        st3.classes.append(cls2)
        cls2.total_student += 1
        # bảng điểm
        cls1_trans1 = Transcript(semester_id=hk1.id,class_id=cls1.id ,subject_detail_id = sd1.id)
        cls1_trans2 = Transcript(semester_id=hk1.id, class_id=cls1.id, subject_detail_id=sd2.id)
        cls1_trans3 = Transcript(semester_id=hk1.id, class_id=cls1.id, subject_detail_id=sd3.id)
        cls2_trans1 = Transcript(semester_id=hk1.id,class_id=cls2.id ,subject_detail_id = sd1.id)
        cls2_trans2 = Transcript(semester_id=hk1.id, class_id=cls2.id, subject_detail_id=sd2.id)
        cls2_trans3 = Transcript(semester_id=hk1.id, class_id=cls2.id, subject_detail_id=sd3.id)
        db.session.add_all([cls1_trans1,cls1_trans2,cls1_trans3,cls2_trans1,cls2_trans2,cls2_trans3])
        db.session.flush()
        # thêm điểm cho lớp cls1_trans1
        sc1 = Score(value=10, type='diem-15-phut', number_Col = 1,transcript_id=cls1_trans1.id,student_id=st1.id)
        sc2 = Score(value=4, type='diem-15-phut', number_Col= 1, transcript_id=cls1_trans1.id, student_id=st2.id)
        sc3 = Score(value=8, type='diem-1-tiet', number_Col = 1,transcript_id=cls1_trans1.id,student_id=st1.id)
        sc4 = Score(value=1, type='diem-1-tiet', number_Col=1, transcript_id=cls1_trans1.id, student_id=st2.id)
        sc5 = Score(value=9, type='diem-thi', number_Col = 1,transcript_id=cls1_trans1.id,student_id=st1.id)
        sc6 = Score(value=3, type='diem-thi', number_Col=1, transcript_id=cls1_trans1.id, student_id=st2.id)
        db.session.add_all([sc1,sc2,sc3,sc4,sc5,sc6])
        # thêm điểm cho lớp cls1_trans2
        sc7 = Score(value=9, type='diem-15-phut', number_Col = 1,transcript_id=cls1_trans2.id,student_id=st1.id)
        sc8 = Score(value=2, type='diem-15-phut', number_Col= 1, transcript_id=cls1_trans2.id, student_id=st2.id)
        sc9 = Score(value=6, type='diem-1-tiet', number_Col = 1,transcript_id=cls1_trans2.id,student_id=st1.id)
        sc10 = Score(value=5, type='diem-1-tiet', number_Col=1, transcript_id=cls1_trans2.id, student_id=st2.id)
        sc11 = Score(value=7, type='diem-thi', number_Col = 1,transcript_id=cls1_trans2.id,student_id=st1.id)
        sc12 = Score(value=2, type='diem-thi', number_Col=1, transcript_id=cls1_trans2.id, student_id=st2.id)
        db.session.add_all([sc7, sc8, sc9, sc10, sc11,sc12])
        # thêm điểm cho lớp cls1_trans3
        sc13 = Score(value=9, type='diem-15-phut', number_Col = 1,transcript_id=cls1_trans3.id,student_id=st1.id)
        sc14 = Score(value=3, type='diem-15-phut', number_Col= 1, transcript_id=cls1_trans3.id, student_id=st2.id)
        sc15 = Score(value=6, type='diem-1-tiet', number_Col = 1,transcript_id=cls1_trans3.id,student_id=st1.id)
        sc16 = Score(value=5, type='diem-1-tiet', number_Col=1, transcript_id=cls1_trans3.id, student_id=st2.id)
        sc17 = Score(value=9, type='diem-thi', number_Col = 1,transcript_id=cls1_trans3.id,student_id=st1.id)
        sc18 = Score(value=3, type='diem-thi', number_Col=1, transcript_id=cls1_trans3.id, student_id=st2.id)
        db.session.add_all([sc13, sc14, sc15, sc16, sc17, sc18])
        # thêm điểm cho lớp cls2_trans1
        sc19 = Score(value=9, type='diem-15-phut', number_Col = 1,transcript_id=cls2_trans1.id,student_id=st3.id)
        sc20 = Score(value=6, type='diem-1-tiet', number_Col = 1,transcript_id=cls2_trans1.id,student_id=st3.id)
        sc21 = Score(value=10, type='diem-thi', number_Col = 1,transcript_id=cls2_trans1.id,student_id=st3.id)
        # thêm điểm cho lớp cls2_trans2
        sc22 = Score(value=9, type='diem-15-phut', number_Col = 1,transcript_id=cls2_trans2.id,student_id=st3.id)
        sc23 = Score(value=10, type='diem-1-tiet', number_Col = 1,transcript_id=cls2_trans2.id,student_id=st3.id)
        sc24 = Score(value=9, type='diem-thi', number_Col = 1,transcript_id=cls2_trans2.id,student_id=st3.id)
        # thêm điểm cho lớp cls2_trans2
        sc25 = Score(value=9, type='diem-15-phut', number_Col = 1,transcript_id=cls2_trans3.id,student_id=st3.id)
        sc26 = Score(value=10, type='diem-1-tiet', number_Col = 1,transcript_id=cls2_trans3.id,student_id=st3.id)
        sc27 = Score(value=9, type='diem-thi', number_Col = 1,transcript_id=cls2_trans3.id,student_id=st3.id)
        db.session.add_all([sc19, sc20, sc21,sc22,sc23,sc24,sc25,sc26,sc27])
        hk1.active = False
        hk2 = Semester(name='2',active=True,academic_year_id=1)
        db.session.add(hk2)
        db.session.flush()
        hk2.classes.append(cls1)
        hk2.classes.append(cls2)
        db.session.commit()



