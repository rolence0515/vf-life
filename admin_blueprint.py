
import hashlib

from flask import Blueprint, render_template, request, jsonify
from lib.login_required import login_required, admin_user_required
from lib.user_repository import UserRepository
from psycopg2 import IntegrityError
from lib.video_repository import VideoRepository

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# ===================================== 一般路由 =====================================
# 管理員使用者頁面
@admin_bp.route('/')
@admin_bp.route('/user')
@admin_user_required
def admin_user():
    return render_template('admin_user.html')

# 影片管理頁面
@admin_bp.route('/videos')
@admin_user_required
def admin_videos():
    return render_template('admin_videos.html')

# 批量開帳號頁面
@admin_bp.route('/bulk_create_accounts')
@admin_user_required
def admin_bulk_create_accounts():
    return render_template('admin_bulk_create_accounts.html')

# ===================================== API 路由 =====================================

# 批量開帳號 - 檔案上傳與批次處理
import csv
import io
import tempfile
from flask import send_file
import hashlib
import datetime

@admin_bp.route('/bulk_create_accounts', methods=['POST'])
@admin_user_required
def api_bulk_create_accounts():
    file = request.files.get('csvFile')
    if not file or not file.filename.endswith('.csv'):
        return jsonify({'error': '請上傳 CSV 檔案'}), 400

    file.stream.seek(0)
    csv_text = file.stream.read().decode('utf-8-sig')
    reader = csv.DictReader(io.StringIO(csv_text))
    result_rows = []
    output = io.StringIO()
    fieldnames = ['name', 'email', 'user_id', 'new_user', 'default_pw', 'videos_count']
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()

    from lib.user_repository import UserRepository
    from lib.video_repository import VideoRepository
    user_repo = UserRepository()
    video_repo = VideoRepository()

    for row in reader:
        name = row.get('name', '').strip()
        email = row.get('email', '').strip().lower()
        serial1 = row.get('serial1', '0').strip()
        serial2 = row.get('serial2', '0').strip()
        new_user = 0
        default_pw = ''
        user = user_repo.get_user_by_email(email)
        if not user:
            # 建立新 user
            pw_raw = hashlib.sha256(email.encode('utf-8')).hexdigest()[:6]
            pw_hash = hashlib.sha256(pw_raw.encode()).hexdigest()
            user_id = user_repo.create_user(name, email, pw_hash)
            new_user = 1
            default_pw = pw_raw
        else:
            user_id = user['id']

        videos_count = 0
        # 處理 serial1/serial2 欄位
        for series_id, serial_flag in [(1, serial1), (2, serial2)]:
            if serial_flag == '1':
                # 查詢該系列所有影片
                videos = video_repo.get_videos_by_series(series_id)
                for v in videos:
                    added = user_repo.add_user_video(user_id, v['id'])
                    if added:
                        videos_count += 1
            elif serial_flag == '0':
                # 移除該系列所有影片權限
                videos = video_repo.get_videos_by_series(series_id)
                for v in videos:
                    user_repo.remove_user_video(user_id, v['id'])

        writer.writerow({
            'name': name,
            'email': email,
            'user_id': user_id,
            'new_user': new_user,
            'default_pw': default_pw,
            'videos_count': videos_count
        })

    user_repo.close()
    video_repo.close()

    # 產生結果 CSV 檔案
    output.seek(0)
    timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
    result_filename = f'bulk_create_result_{timestamp}.csv'
    result_path = tempfile.mktemp(suffix='.csv')
    with open(result_path, 'w', encoding='utf-8-sig') as f:
        f.write(output.getvalue())

    # 回傳下載連結（不回傳表格）
    from flask import url_for
    return jsonify({
        'result_csv_url': url_for('admin.download_bulk_create_result', filename=result_filename)
    })

# 提供結果 CSV 檔案下載
@admin_bp.route('/bulk_create_result/<filename>')
@admin_user_required
def download_bulk_create_result(filename):
    import os
    import glob
    # 只允許下載剛剛產生的檔案
    temp_dir = tempfile.gettempdir()
    file_path = os.path.join(temp_dir, filename)
    if not os.path.exists(file_path):
        # fallback: 找最新的 bulk_create_result_*.csv
        files = sorted(glob.glob(os.path.join(temp_dir, 'bulk_create_result_*.csv')), reverse=True)
        if files:
            file_path = files[0]
        else:
            return 'File not found', 404
    return send_file(file_path, as_attachment=True, download_name=filename)
# 新增/移除管理員 API
@admin_bp.route('/api/users/<int:user_id>/toggle_admin', methods=['POST'])
@admin_user_required
def api_toggle_admin(user_id):
    repo = UserRepository()
    try:
        user = repo.get_user_by_id(user_id)
        if not user:
            return jsonify({'success': False, 'msg': '找不到使用者'}), 404
        data = request.get_json() or {}
        action = data.get('action')
        if action == 'add':
            # 新增管理員
            try:
                repo.add_admin(user_id)
                return jsonify({'success': True, 'msg': f"{user['email']} 已設為管理員"})
            except IntegrityError:
                repo.conn.rollback()
                return jsonify({'success': False, 'msg': '已是管理員'}), 400
        elif action == 'remove':
            # 移除管理員前，檢查剩餘管理員數量
            admin_count = repo.get_admin_count()
            if admin_count <= 1:
                return jsonify({'success': False, 'msg': '至少需保留一位管理員，無法全部移除'}), 400
            repo.remove_admin(user_id)
            return jsonify({'success': True, 'msg': f"{user['email']} 已取消管理員身份"})
        else:
            return jsonify({'success': False, 'msg': '未知操作'}), 400
    finally:
        repo.close()

# 取得使用者列表 (支援 email/name like 搜尋)
@admin_bp.route('/api/users', methods=['GET'])
@admin_user_required
def api_get_users():
    q = request.args.get('q', '').strip().lower()
    offset = int(request.args.get('offset', 0))
    limit = int(request.args.get('limit', 100))
    repo = UserRepository()
    try:
        users, total = repo.get_users_with_pagination(q, offset, limit)
        return jsonify({'users': users, 'total': total})
    finally:
        repo.close()

# 設為預設密碼 (假設預設密碼為 '12345678')
@admin_bp.route('/api/users/<int:user_id>/reset_password', methods=['POST'])
@admin_user_required
def api_reset_password(user_id):
    # 這裡應該要查詢資料庫並更新密碼
    repo = UserRepository()
    try:
        user = repo.get_user_by_id(user_id)
        if not user:
            raise Exception('找不到使用者')
        else:
            email = user['email']
        # 預設密碼規則: sha256(email)[:6]
        default_pw = hashlib.sha256(email.encode('utf-8')).hexdigest()[:6]
        pw = hashlib.sha256(default_pw.encode()).hexdigest()
        repo.update_password(user_id, pw)
        return jsonify({'success': True, 'msg': f"已將 {email} 密碼設為預設值", 'default_pw': default_pw})
    finally:
        repo.close()

# @admin_bp.route('/user_videos')
# @admin_user_required
# def admin_user_videos():
#     return render_template('admin_user_videos.html')

# @admin_bp.route('/series')
# @admin_user_required
# def admin_series():
#     return render_template('admin_series.html')

# 取得影片列表 API
@admin_bp.route('/api/videos', methods=['GET'])
@admin_user_required
def api_get_videos():
    repo = VideoRepository()
    try:
        videos = repo.get_all_videos()
        return jsonify({'success': True, 'videos': videos})
    finally:
        repo.close()

# 新增或編輯影片 API
@admin_bp.route('/api/videos', methods=['POST'])
@admin_user_required
def api_create_or_update_video():
    data = request.get_json() or {}
    repo = VideoRepository()
    try:
        video_id = data.get('id')
        if video_id:
            # 編輯
            updated = repo.update_video(video_id, data)
            return jsonify({'success': updated, 'msg': '影片已更新' if updated else '更新失敗'})
        else:
            # 新增
            try:
                new_id = repo.create_video(data)
                if new_id:
                    return jsonify({'success': True, 'id': new_id, 'msg': '影片已新增'})
                else:
                    return jsonify({'success': False, 'msg': '新增失敗，請檢查資料內容'}), 400
            except Exception as e:
                return jsonify({'success': False, 'msg': f'新增失敗：{str(e)}'}), 400
    finally:
        repo.close()

# 刪除影片 API
@admin_bp.route('/api/videos/<int:video_id>', methods=['DELETE'])
@admin_user_required
def api_delete_video(video_id):
    repo = VideoRepository()
    try:
        deleted = repo.delete_video(video_id)
        return jsonify({'success': deleted, 'msg': '影片已刪除' if deleted else '刪除失敗'})
    finally:
        repo.close()

# 取得系列列表 API
@admin_bp.route('/api/series', methods=['GET'])
@admin_user_required
def api_get_series():
    repo = VideoRepository()
    try:
        series = repo.get_all_series()
        return jsonify({'success': True, 'series': series})
    finally:
        repo.close()

# @admin_bp.route('/admin_users')
# @admin_user_required
# def admin_admin_users():
#     return render_template('admin_admin_users.html')

@admin_bp.app_errorhandler(404)
def admin_page_not_found(e):
    return render_template('admin_404.html'), 404