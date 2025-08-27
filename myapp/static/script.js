//Đóng sidebar
    const bntClick = document.querySelector(".toggle-btn");
    bntClick.addEventListener("click", function () {
      document.querySelector("#sidebar").classList.toggle("hidden");
    });
//Khởi tạo Tooltip cho tất cả các phần tử có data-bs-toggle="tooltip"
  var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'))
  var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
    return new bootstrap.Tooltip(tooltipTriggerEl, {
      placement: 'top',
      trigger: 'hover focus'
    })
  })
//thay đổi ảnh
let preview = document.querySelector(".img");
let file = document.getElementById("avatar")
file.onchange = function () {
    if (file.files[0].size < 1000000) { // Kiểm tra kích thước file
        let fileReader = new FileReader(); // Tạo đối tượng FileReader
        fileReader.onload = function (e) {
            let imgURL = e.target.result; // Lấy URL ảnh sau khi đọc
            preview.src = imgURL; // Gán URL cho thuộc tính src của ảnh
            avatar.src = imgURL;
        };
        fileReader.readAsDataURL(file.files[0]); // Đọc file
    } else {
        alert ("File kích thước quá lớn!"); // Thông báo lỗi
    }
};
//ẩn alert sau 3s
setTimeout(function() {
     var alert = document.querySelector(".alert");
     alert.style.display = "none";
}, 3000);
//Gui du lieu
function selectRow(subject_id, class_id) {
     window.location.href = '/chitietmon/'+class_id+'?subject_id=' + subject_id;
}
function clickAdd(class_id, total_student){
    if (total_student >= 40)
        alert('Lớp đã đủ !');
    else
        window.location.href ='/themhocsinh/'+class_id
}
function selectSubject(selectElement){
    let subject_id = selectElement.value;
    if(subject_id)
        window.location.href = '/diem/?subject='+subject_id;
}
function clickSearch(subject_id,class_id){
    let searchText = document.getElementById('searchText').value;
    window.location.href ='/nhapdiem/'+subject_id+'?class_id='+class_id+'&search='+searchText
}
//xoá học sinh
function deleteStudent(studentId) {
    if (confirm('Bạn có chắc chắn muốn xoá học sinh này không?')) {
                fetch(`/api/delete_student/${studentId}`, {
                method: 'DELETE'})
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        alert('Xoá học sinh thành công!');
                        document.getElementById('classForm').submit();
                    } else {
                        alert('Xoá học sinh thất bại!');
                    }
                })
                .catch(error => {
                    console.error('Lỗi:', error);
                    alert('Đã xảy ra lỗi khi xoá học sinh.');
                });
            }
}
//thêm học sinh vào lớp
function addStudent(studentId, classId, total_student) {
    if (confirm('Bạn có chắc chắn muốn thêm học sinh này không?')) {
                fetch('/api/add-student', {
                method: 'POST',
                body: JSON.stringify({
                    'student_id': studentId,
                    'class_id': classId
                }),
                headers: {
                    'Content-Type': 'application/json'
                }
                })
                .then(function(res){
                return res.json();
                })
                .then(function(data) {
                    if (data.content == 'Thêm học sinh thành công') {
                        alert(data.content);
                        location.reload();
                    } else {
                        alert(data.content);
                    }
                })
                .catch(function(error){
                    console.error('Lỗi:', error);
                    alert('Đã xảy ra lỗi khi thêm học sinh.');
                });
            }
}
//thêm cột điểm
function addColumn(transcript_id,type_score){
     fetch('/api/add-column', {
                method: 'POST',
                body: JSON.stringify({
                    'transcript_id': transcript_id,
                    'type_score': type_score
                }),
                headers: {
                    'Content-Type': 'application/json'
                }
                })
                .then(function(res){
                return res.json();
                })
                .then(function(data) {
                    if (data.content == 'Thêm thành công') {
                        alert(data.content);
                        location.reload();
                    } else {
                        alert(data.content);
                    }
                })
     }
//Nhap diem
 function saveScore(transcript_id) {
    const table = document.getElementById("scoreTable");
    const rows = table.querySelectorAll("tbody tr");
    const scores = [];
    rows.forEach((row) => {
        const studentId = row.dataset.studentId;
        const diem15Phut = [];
        const diem1Tiet = [];
        // Lấy điểm 15 phút
        row.querySelectorAll(".diem-15-phut").forEach((cell) => {
            const value = parseFloat(cell.textContent.trim());
            if (!isNaN(value)) {
                diem15Phut.push({ lan: cell.dataset.lan, value }); }
        });
        // Lấy điểm 1 tiết
        row.querySelectorAll(".diem-1-tiet").forEach((cell) => {
            const value = parseFloat(cell.textContent.trim());
            if (!isNaN(value)) {
                diem1Tiet.push({ lan: cell.dataset.lan, value });
            }
        });
        // Lấy điểm thi
        const diemThiCell = row.querySelector(".diem-thi");
        const diemThi = diemThiCell ? parseFloat(diemThiCell.textContent.trim()) : null;

        scores.push({
            student_id: studentId,
            diem_15_phut: diem15Phut,
            diem_1_tiet: diem1Tiet,
            diem_thi: diemThi,
            });
         });
        if (scores.length === 0) {
            alert("Hãy nhập điểm.");
            return;
        }
        fetch('/api/save-score', {
                method: 'POST',
                body: JSON.stringify({
                    'transcript_id': transcript_id,
                    'scores': scores
                }),
                headers: {
                    'Content-Type': 'application/json'
                }
                })
                .then(function(res){
                return res.json();
                })
                .then(function(data) {
                    if (data.content == 'Lưu điểm thành công') {
                        alert(data.content);
                        location.reload();
                    } else {
                        alert('Lưu điểm thất bại');
                    }
                })
                .catch(function(error){
                    console.error('Lỗi:', error);
                    alert('Đã xảy ra lỗi khi lưu điểm.');
                });
        }
//ràng buộc điểm
function validateInput(cell) {
    const value = parseFloat(cell.innerText.trim());
    if (value != null && (value < 0 || value > 10)) {
        alert("Điểm phải trong khoảng từ 0 đến 10.");
        cell.innerText = '';
    }
}
//check chọn cả 3 select sẽ submit form
function checkSelected(){
    const selects = document.querySelectorAll('.output-score');
    const form = document.getElementById('final-score-form');
    let allSelected = true;
    selects.forEach(select => {
        if (select.value == '')
            allSelected = false;
    });
    if (allSelected)
        form.submit();
}




