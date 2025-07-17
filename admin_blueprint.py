import hashlib
import os
import glob
import csv
import io
import tempfile
import hashlib
import datetime

from flask import Blueprint, render_template, request, jsonify, url_for, send_file, session
from lib.login_required import login_required, admin_user_required
from psycopg2 import IntegrityError
from lib.user_repository import UserRepository
from lib.video_repository import VideoRepository
from lib.batch_account_log_repository import BatchAccountLogRepository
from lib.series_repository import SeriesRepository
from lib.gcs_upload import upload_file_to_gcs

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

# 批量開帳號頁面
@admin_bp.route('/bulk_create_accounts_v2')
@admin_user_required
def admin_bulk_create_accounts_v2():
    return render_template('admin_bulk_create_accounts_v2.html')

@admin_bp.route('/batch_account_log')
@admin_user_required
def admin_batch_account_log():
    repo = BatchAccountLogRepository()
    logs = repo.get_recent_logs(20)
    repo.close()
    return render_template('admin_batch_account_log.html', logs=logs)

# 影片系列列表頁面
@admin_bp.route('/series')
@admin_user_required
def admin_series():
    return render_template('admin_series.html')

# 使用者影片列表頁（僅管理員可檢視）
@admin_bp.route('/user_videos/<int:user_id>')
@admin_user_required
def admin_user_videos(user_id):
    repo = UserRepository()
    user = repo.get_user_by_id(user_id)
    if not user:
        repo.close()
        return render_template('admin_404.html'), 404
    # 取得該使用者已開通的所有影片
    video_list = repo.get_user_videos(user_id)
    repo.close()
    # 傳給前端
    return render_template('admin_user_videos.html', videoList=video_list, userInfo=user)

# ===================================== API 路由 =====================================

# 批量開帳號 - 檔案上傳與批次處理
@admin_bp.route('/bulk_create_accounts', methods=['POST'])
@admin_user_required
def api_bulk_create_accounts():
    file = request.files.get('csvFile')
    if not file or not file.filename.endswith('.csv'):
        return jsonify({'error': '請上傳 CSV 檔案'}), 400

    dry_run = request.form.get('dry_run') == '1'
    file.stream.seek(0)
    csv_text = file.stream.read().decode('utf-8-sig')
    reader = csv.DictReader(io.StringIO(csv_text))
    result_rows = []
    output = io.StringIO()
    fieldnames = ['name', 'email', 'user_id', 'new_user', 'default_pw', 'videos_count']
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()

    user_repo = UserRepository()
    video_repo = VideoRepository()

    # 取得操作者資訊（假設 session 有存姓名與 email）
    operator_name = None
    operator_email = None
    try:
        operator_email = session.get('user_email') or ''
        user = user_repo.get_user_by_email(operator_email)
        operator_name = user['name'] if user and 'name' in user else ''
    except Exception:
        pass

    backup_checked = True # 前端必定已勾選「已通知備份」才可能進入這個 API
    log_repo = BatchAccountLogRepository()
    status = 'success'
    fail_reason = ''
    total_count = 0
    new_user_count = 0
    exist_user_count = 0
    total_videos_count = 0

    try:
        for row in reader:
            name = row.get('name', '').strip()
            email = row.get('email', '').strip().lower()
            serial1 = row.get('serial1', '').strip()
            serial2 = row.get('serial2', '').strip()
            # 驗證必填欄位
            if not name or not email or not serial1 or not serial2:
                raise ValueError(f"CSV 欄位缺漏或空值，請檢查 name/email/serial1/serial2，錯誤資料: {row}")

            new_user = 0
            default_pw = ''
            user = user_repo.get_user_by_email(email)
            user_id = None
            if not user:
                # 建立新 user（dry-run 不寫入）
                pw_raw = hashlib.sha256(email.encode('utf-8')).hexdigest()[:6]
                pw_hash = hashlib.sha256(pw_raw.encode()).hexdigest()
                if not dry_run:
                    user_id = user_repo.create_user(name, email, pw_hash)
                else:
                    user_id = f"(new)"
                new_user = 1
                default_pw = pw_raw
            else:
                user_id = user['id']

            videos_count = 0
            # 處理 serial1/serial2 欄位
            for series_id, serial_flag in [(1, serial1), (2, serial2)]:
                if serial_flag == '1':
                    videos = video_repo.get_videos_by_series(series_id)
                    for v in videos:
                        if not dry_run:
                            added = user_repo.add_user_video(user_id, v['id'])
                            if added:
                                videos_count += 1
                        else:
                            videos_count += 1
                elif serial_flag == '0':
                    videos = video_repo.get_videos_by_series(series_id)
                    for v in videos:
                        if not dry_run:
                            user_repo.remove_user_video(user_id, v['id'])

            writer.writerow({
                'name': name,
                'email': email,
                'user_id': user_id,
                'new_user': new_user,
                'default_pw': default_pw,
                'videos_count': videos_count
            })

            # 統計資訊
            total_count += 1
            if new_user:
                new_user_count += 1
            else:
                exist_user_count += 1
            total_videos_count += videos_count

        if dry_run:
            return jsonify({'success': True})

        user_repo.close()
        video_repo.close()

        # 產生結果 CSV 檔案（直接用 bulk_create_result_yyyyMMddHHmmss.csv 寫入 tempdir）
        output.seek(0)
        timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
        result_filename = f'bulk_create_result_{timestamp}.csv'
        result_path = os.path.join(tempfile.gettempdir(), result_filename)
        with open(result_path, 'w', encoding='utf-8-sig') as f:
            f.write(output.getvalue())

        # === 上傳到 GCS ===
        bucket_name = 'bulk_create_accounts'
        gcs_path = f'logs/{result_filename}'
        gcs_url = ''
        try:
            gcs_url = upload_file_to_gcs(result_path, bucket_name, gcs_path, content_type='text/csv')
        except Exception as e:
            gcs_url = ''  # 若上傳失敗不影響本地下載，但不回傳 GCS 連結

        # 寫入批量log
        log_repo.insert_log(
            operator_name=operator_name,
            operator_email=operator_email,
            backup_checked=backup_checked,
            status=status,
            fail_reason=fail_reason,
            total_count=total_count,
            new_user_count=new_user_count,
            exist_user_count=exist_user_count,
            total_videos_count=total_videos_count,
            result_filename=result_filename,
            gcs_url=gcs_url
        )
        log_repo.close()

        return jsonify({
            'result_csv_url': gcs_url,  # 直接給 GCS 下載網址
            'gcs_url': gcs_url
        })
    except Exception as e:
        status = 'fail'
        fail_reason = str(e)
        if not dry_run:
            # 寫入失敗log
            log_repo.insert_log(
                operator_name=operator_name,
                operator_email=operator_email,
                backup_checked=backup_checked,
                status=status,
                fail_reason=fail_reason,
                total_count=total_count,
                new_user_count=new_user_count,
                exist_user_count=exist_user_count,
                total_videos_count=total_videos_count,
                result_filename='',
                gcs_url=''
            )
            log_repo.close()
        if dry_run:
            return jsonify({'success': False, 'error': str(e)})
        return jsonify({'error': str(e)}), 500
    
#請插在這裏

# 新版批量會員影片/系列開通 - CSV 格式
@admin_bp.route('/bulk_create_accounts_v2', methods=['POST'])
@admin_user_required
def api_bulk_create_accounts_v2():
    file = request.files.get('csvFile')
    if not file or not file.filename.endswith('.csv'):
        return jsonify({'error': '請上傳 CSV 檔案'}), 400

    dry_run = request.form.get('dry_run') == '1'
    file.stream.seek(0)
    csv_text = file.stream.read().decode('utf-8-sig')
    reader = csv.DictReader(io.StringIO(csv_text))
    output = io.StringIO()
    fieldnames = ['user_email', 'user_id', 'new_user', 'default_pw', 'opened_series', 'opened_videos', 'videos_count', 'error']
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()

    user_repo = UserRepository()
    video_repo = VideoRepository()
    series_repo = SeriesRepository()

    # 取得操作者資訊（假設 session 有存姓名與 email）
    operator_name = None
    operator_email = None
    try:
        operator_email = session.get('user_email') or ''
        user = user_repo.get_user_by_email(operator_email)
        operator_name = user['name'] if user and 'name' in user else ''
    except Exception:
        pass

    # 前端必定已勾選「已通知備份」才可能進入這個 API
    backup_checked = True
    log_repo = BatchAccountLogRepository()
    status = 'success'
    fail_reason = ''
    total_count = 0
    new_user_count = 0
    exist_user_count = 0
    total_videos_count = 0

    try:
        dry_run_errors = []
        for row in reader:
            email = (row.get('user_email') or '').strip().lower()
            series_ids_raw = (row.get('series_ids') or '').strip()
            video_ids_raw = (row.get('video_ids') or '').strip()
            error_msg = ''
            opened_series = []
            opened_videos = []
            videos_count = 0

            if not email:
                # 缺少 email 欄位
                error_msg = '缺少 user_email'
                writer.writerow({
                    'user_email': email,
                    'user_id': '',
                    'new_user': '',
                    'default_pw': '',
                    'opened_series': '',
                    'opened_videos': '',
                    'videos_count': '',
                    'error': error_msg
                })
                dry_run_errors.append(error_msg)
                continue

            # 解析 series_ids, video_ids
            series_ids = [s.strip() for s in series_ids_raw.split(',') if s.strip()] if series_ids_raw else []
            video_ids = [v.strip() for v in video_ids_raw.split(',') if v.strip()] if video_ids_raw else []

            new_user = 0
            default_pw = ''
            user = user_repo.get_user_by_email(email)
            user_id = None
            if not user:
                # 建立新 user（dry-run 不寫入）
                # 預設密碼規則: sha256(email)[:6]
                pw_raw = hashlib.sha256(email.encode('utf-8')).hexdigest()[:6]
                pw_hash = hashlib.sha256(pw_raw.encode()).hexdigest()
                if not dry_run:
                    user_id = user_repo.create_user(email, email, pw_hash)
                else:
                    user_id = '(new)'
                new_user = 1
                default_pw = pw_raw
            else:
                # 已存在的使用者
                user_id = user['id']

            # 開通系列
            for sid in series_ids:
                try:
                    sid_int = int(sid)
                    videos = video_repo.get_videos_by_series(sid_int)
                    if not videos:
                        # 系列下無影片
                        error_msg += f'系列ID {sid} 無影片; '
                        dry_run_errors.append(f'系列ID {sid} 無影片')
                        continue

                    opened_series.append(sid)
                    # 開通系列下的所有影片
                    for v in videos: 
                        if not dry_run:
                            added = user_repo.add_user_video(user_id, v['id'])
                            if added:
                                videos_count += 1
                        else:
                            videos_count += 1
                        opened_videos.append(str(v['id']))
                except Exception as e:
                    error_msg += f'系列ID {sid} 錯誤: {str(e)}; '
                    dry_run_errors.append(f'系列ID {sid} 錯誤: {str(e)}')

            # 開通指定影片
            for vid in video_ids:
                try:
                    vid_int = int(vid)
                    video = video_repo.get_video_by_id(vid_int)
                    if not video:
                        # 影片不存在
                        error_msg += f'影片ID {vid} 不存在; '
                        dry_run_errors.append(f'影片ID {vid} 不存在')
                        continue
                    if not dry_run:
                        # 開通影片
                        added = user_repo.add_user_video(user_id, vid_int)
                        if added:
                            videos_count += 1
                    else:
                        videos_count += 1
                    opened_videos.append(str(vid_int))
                except Exception as e:
                    error_msg += f'影片ID {vid} 錯誤: {str(e)}; '
                    dry_run_errors.append(f'影片ID {vid} 錯誤: {str(e)}')

            # 若 series_ids 和 video_ids 都空，略過
            if not series_ids and not video_ids:
                error_msg += '未指定任何系列或影片; '
                dry_run_errors.append('未指定任何系列或影片')

            writer.writerow({
                'user_email': email,
                'user_id': user_id,
                'new_user': new_user,
                'default_pw': default_pw,
                'opened_series': ','.join(opened_series),
                'opened_videos': ','.join(opened_videos),
                'videos_count': videos_count,
                'error': error_msg
            })

            total_count += 1
            if new_user:
                new_user_count += 1
            else:
                exist_user_count += 1
            total_videos_count += videos_count

        if dry_run:
            # 只做測試，不寫入資料庫，到這裡就結束
            if dry_run_errors:
                return jsonify({'success': False, 'error': 'CSV 驗證失敗：' + '; '.join(dry_run_errors)})
            return jsonify({'success': True})

        # 關閉資料庫連線
        user_repo.close()
        video_repo.close()
        series_repo.close()

        # 產生結果 CSV 檔案（直接用 bulk_create_result_v2_yyyyMMddHHmmss.csv 寫入 tempdir）
        output.seek(0)
        timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
        result_filename = f'bulk_create_result_v2_{timestamp}.csv'
        result_path = os.path.join(tempfile.gettempdir(), result_filename)
        with open(result_path, 'w', encoding='utf-8-sig') as f:
            f.write(output.getvalue())

        # 上傳到 GCS
        bucket_name = 'bulk_create_accounts'
        gcs_path = f'logs/{result_filename}'
        gcs_url = ''
        try:
            gcs_url = upload_file_to_gcs(result_path, bucket_name, gcs_path, content_type='text/csv')
        except Exception as e:
            gcs_url = ''

        # 寫入批量log
        log_repo.insert_log(
            operator_name=operator_name,
            operator_email=operator_email,
            backup_checked=backup_checked,
            status=status,
            fail_reason=fail_reason,
            total_count=total_count,
            new_user_count=new_user_count,
            exist_user_count=exist_user_count,
            total_videos_count=total_videos_count,
            result_filename=result_filename,
            gcs_url=gcs_url
        )
        log_repo.close()

        return jsonify({
            'result_csv_url': gcs_url,
            'gcs_url': gcs_url
        })
    except Exception as e:
        status = 'fail'
        fail_reason = str(e)
        if not dry_run:
            log_repo.insert_log(
                operator_name=operator_name,
                operator_email=operator_email,
                backup_checked=backup_checked,
                status=status,
                fail_reason=fail_reason,
                total_count=total_count,
                new_user_count=new_user_count,
                exist_user_count=exist_user_count,
                total_videos_count=total_videos_count,
                result_filename='',
                gcs_url=''
            )
            log_repo.close()
        if dry_run:
            return jsonify({'success': False, 'error': str(e)})
        return jsonify({'error': str(e)}), 500

# 已移除 /bulk_create_result/<filename> 路由，下載請直接用 GCS 連結
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
    admin_only = request.args.get('admin_only', '0') == '1'
    repo = UserRepository()
    try:
        users, total = repo.get_users_with_pagination(q, offset, limit, admin_only=admin_only)
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
    except Exception as e:
        # 特別處理外鍵約束錯誤，顯示友善中文訊息
        err_msg = str(e)
        if 'violates foreign key constraint' in err_msg and 'user_videos_video_id_fkey' in err_msg:
            return jsonify({'success': False, 'msg': '有使用者擁有此影片，請先移除所有使用者後再刪除'}), 400
        return jsonify({'success': False, 'msg': err_msg}), 400
    finally:
        repo.close()

@admin_bp.route('/api/series', methods=['GET'])
@admin_user_required
def api_get_series():
    repo = SeriesRepository()
    try:
        series = repo.get_all_series()
        return jsonify({'success': True, 'series': series})
    finally:
        repo.close()

@admin_bp.route('/api/series', methods=['POST'])
@admin_user_required
def api_create_series():
    data = request.get_json() or {}
    name = data.get('name', '').strip()
    description = data.get('description', '').strip()
    if not name:
        return jsonify({'success': False, 'msg': '系列名稱不可為空'}), 400
    repo = SeriesRepository()
    try:
        new_id = repo.create_series(name, description)
        return jsonify({'success': True, 'id': new_id, 'msg': '系列已新增'})
    finally:
        repo.close()

@admin_bp.route('/api/series/<int:series_id>', methods=['PUT'])
@admin_user_required
def api_update_series(series_id):
    data = request.get_json() or {}
    name = data.get('name', '').strip()
    description = data.get('description', '').strip()
    if not name:
        return jsonify({'success': False, 'msg': '系列名稱不可為空'}), 400
    repo = SeriesRepository()
    try:
        updated = repo.update_series(series_id, name, description)
        return jsonify({'success': updated, 'msg': '系列已更新' if updated else '更新失敗'})
    finally:
        repo.close()

@admin_bp.route('/api/series/<int:series_id>', methods=['DELETE'])
@admin_user_required
def api_delete_series(series_id):
    # 先檢查該系列下是否有影片
    vrepo = VideoRepository()
    try:
        videos = vrepo.get_videos_by_series(series_id)
        if videos and len(videos) > 0:
            return jsonify({'success': False, 'msg': '此系列下仍有影片，請先移除所有影片後再刪除系列'}), 400
    finally:
        vrepo.close()
    repo = SeriesRepository()
    try:
        deleted = repo.delete_series(series_id)
        return jsonify({'success': deleted, 'msg': '系列已刪除' if deleted else '刪除失敗'})
    finally:
        repo.close()

@admin_bp.route('/api/user_videos/<int:user_id>/series_and_videos', methods=['GET'])
@admin_user_required
def api_user_series_and_videos(user_id):
    # 取得所有系列及該系列下所有影片，並標記該 user 已擁有的影片
    srepo = SeriesRepository()
    vrepo = VideoRepository()
    urepo = UserRepository()
    all_series = srepo.get_all_series()
    all_videos = vrepo.get_all_videos()
    user_videos = set(v['id'] for v in urepo.get_user_videos(user_id))
    srepo.close()
    vrepo.close()
    urepo.close()
    # 組合資料
    series_list = []
    for s in all_series:
        videos = [
            {
                'id': v['id'],
                'title': v['title'],
                'owned': v['id'] in user_videos
            }
            for v in all_videos if v['series_id'] == s['id']
        ]
        series_list.append({
            'id': s['id'],
            'name': s['name'],
            'videos': videos
        })
    return jsonify({'success': True, 'series': series_list})

@admin_bp.route('/api/user_videos/<int:user_id>/add', methods=['POST'])
@admin_user_required
def api_add_user_video(user_id):
    data = request.get_json() or {}
    video_id = data.get('video_id')
    if not video_id:
        return jsonify({'success': False, 'msg': '缺少影片ID'}), 400
    from lib.user_repository import UserRepository
    repo = UserRepository()
    try:
        added = repo.add_user_video(user_id, video_id)
        return jsonify({'success': added, 'msg': '已新增' if added else '已存在'})
    finally:
        repo.close()

@admin_bp.route('/api/user_videos/<int:user_id>/remove', methods=['POST'])
@admin_user_required
def api_remove_user_video(user_id):
    data = request.get_json() or {}
    video_id = data.get('video_id')
    if not video_id:
        return jsonify({'success': False, 'msg': '缺少影片ID'}), 400
    from lib.user_repository import UserRepository
    repo = UserRepository()
    try:
        repo.remove_user_video(user_id, video_id)
        return jsonify({'success': True, 'msg': '已刪除'})
    finally:
        repo.close()

# ===================================== 錯誤處理 =====================================

@admin_bp.app_errorhandler(404)
def admin_page_not_found(e):
    return render_template('admin_404.html'), 404