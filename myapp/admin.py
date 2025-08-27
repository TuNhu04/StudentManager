from flask_admin import Admin, BaseView, expose, AdminIndexView
from flask_login import logout_user, current_user
from flask import redirect, request, url_for, flash
from flask_admin.contrib.sqla import ModelView
from sqlalchemy.exc import IntegrityError
from models import Subject, Rule, Role, User, Semester, AcademicYear, Transcript, Class, SubjectDetail
from myapp import app, dao, db, login
import json, hashlib

login.login_view = 'login_account'

class MySubjectView(ModelView):
    # Đảm bảo người dùng có quyền truy cập
    def is_accessible(self):
        return current_user.is_authenticated and current_user.role == Role.ADMIN
    # Các cột hiển thị và tìm kiếm
    column_list = ['id', 'name']
    column_searchable_list = ['name']
    def on_model_change(self, form, model, is_created):
        try:
            db.session.commit()  # Lưu thay đổi vào cơ sở dữ liệu
        except IntegrityError:
            db.session.rollback()  # Hủy bỏ thay đổi nếu có lỗi
            raise IntegrityError('Tên môn học đã tồn tại!', None, None)
    def on_model_delete(self, model):
        if model.teachers:
            for subject_detail in model.teachers:
                if subject_detail.classes:
                    flash('Không thể xóa môn học vì đã có giáo viên phân công giảng dạy.', 'error')
                    return redirect(url_for('subject.index_view'))  # Quay lại trang danh sách môn học
        else:
            try:
                db.session.delete(model)  # Xóa môn học nếu không có phân công giáo viên
                db.session.commit()
            except IntegrityError:
                db.session.rollback()
                flash('Có lỗi xảy ra khi xóa môn học.', 'error')
                return redirect(url_for('subject.index_view'))

class AdminModelView(ModelView):
    def is_accessible(self):
        return current_user.is_authenticated and current_user.role == Role.ADMIN
    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('login_account'))
    def on_model_change(self, form, model, is_created):
        if 'password' in form.data and form.data['password']:
            model.password = str(hashlib.md5('password'.encode('utf-8')).hexdigest())
        if model.name == 'maxAge':
            min_age = Rule.query.filter_by(name='minAge').first()
            if min_age and model.value <= min_age.value:
                raise ValueError("Tuổi lớn nhất (maxAge) phải lớn hơn tuổi nhỏ nhất (minAge)!")
        if model.name == 'minAge':
            max_age = Rule.query.filter_by(name='maxAge').first()
            if max_age and model.value >= max_age.value:
                raise ValueError("Tuổi nhỏ nhất (minAge) phải nhỏ hơn tuổi lớn nhất (maxAge)!")

class LogoutView(BaseView):
    @expose('/')
    def index(self):
        logout_user()
        return redirect('/')
    def is_accessible(self):
        return current_user.is_authenticated

class MyAdminIndex(AdminIndexView):
    @expose()
    def index(self):
        count_student = dao.count_student()
        count_teacher = dao.count_teacher()
        count_grade10 = dao.count_grade(10)
        count_grade11 = dao.count_grade(11)
        count_grade12 = dao.count_grade(12)
        semester = dao.active_semester()
        year = dao.get_academicyear(academicyear_id=semester.academic_year_id).name
        return self.render('admin/index.html',count_student=count_student,
                           count_teacher=count_teacher,
                           count_grade10=count_grade10,
                           count_grade11=count_grade11,
                           count_grade12=count_grade12,
                           semester=semester.name,
                           year=year)

class ReportView(BaseView):
    @expose('/')
    def index(self):
        subjects = Subject.query.all()
        academic_years = AcademicYear.query.all()
        return self.render('admin/report_form.html',subjects=subjects,academic_years=academic_years)

    @expose('generate_report', methods=['POST'])
    def generate_report(self):
        subject_id = request.form.get('subject')
        semester_id = request.form.get('semester')
        academic_year_id = request.form.get('academic_year')

        #Lấy thông tin
        subject = Subject.query.get(subject_id)
        semester = Semester.query.get(semester_id)
        academic_year = AcademicYear.query.get(academic_year_id)

        classes = db.session.query(Class).join(Transcript, Class.id == Transcript.class_id).join(SubjectDetail, Transcript.subject_detail_id == SubjectDetail.id).filter(SubjectDetail.subject_id == subject_id,Transcript.semester_id == semester_id).all()
        if not classes:
            return self.render('admin/report_result.html',
                               subject=subject,
                               semester=semester,
                               academic_year=academic_year,
                               message="Không có dữ liệu cho môn học hoặc học kỳ đã chọn.")
        report_data = []
        for subject_details in classes:
            transcripts = Transcript.query.filter_by(subject_detail_id=subject_id, semester_id=semester_id, class_id=subject_details.id).all()
            total_students = len(subject_details.students)
            students_passed = 0
            for student in subject_details.students:
                final_scores = []
                for transcript in transcripts:
                    scores_15p = [s.value for s in transcript.scores if s.student_id == student.id and s.type == 'diem-15-phut']
                    scores_1t = [s.value for s in transcript.scores if s.student_id == student.id and s.type == 'diem-1-tiet']
                    scores_ck = [s.value for s in transcript.scores if s.student_id == student.id and s.type == 'diem-thi']
                    sum_15p = sum(scores_15p)
                    sum_1t = sum(scores_1t)
                    ck = scores_ck[0] if scores_ck else 0
                    number15Col = transcript.number15Col or 1
                    number1Col = transcript.number1Col or 1
                    final_avg = (sum_15p + sum_1t * 2 + ck * 3) / (number15Col + number1Col * 2 + 3)

                    final_scores.append(final_avg)
                if any(score >= 5 for score in final_scores):
                    students_passed += 1
            pass_rate = (students_passed / total_students) * 100 if total_students else 0
            report_data.append({
                "class_name": subject_details.name,
                "total_students": total_students,
                "students_passed": students_passed,
                "pass_rate": pass_rate
            })
            report_data_with_index = list(enumerate(report_data))
            # Dữ liệu cho biểu đồ
            labels = [data['class_name'] for data in report_data]
            pass_rates = [data['pass_rate'] for data in report_data]
        return self.render('admin/report_result.html',
                           subject=subject,
                            semester=semester,
                            academic_year=academic_year,
                            report_data=report_data_with_index,
                            labels=json.dumps(labels),
                            pass_rates=json.dumps(pass_rates))

    def is_accessible(self):
        return current_user.is_authenticated and current_user.role == Role.ADMIN


admin = Admin(app, name="QUẢN LÝ HỌC SINH",template_mode='bootstrap4', index_view=MyAdminIndex())
admin.add_view(AdminModelView(User, db.session))
admin.add_view(AdminModelView(Rule, db.session))
admin.add_view(MySubjectView(Subject,db.session))
admin.add_view(ReportView(name='Report', endpoint='report'))
admin.add_view(LogoutView(name='Logout'))
