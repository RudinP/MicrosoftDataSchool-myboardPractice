import os
import psycopg2
from psycopg2.extras import DictCursor
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from dotenv import load_dotenv
from datetime import datetime
import json
import folium

# 로컬 환경에서는 .env를 읽고, Azure에서는 패스.
if os.path.exists('.env'):
    load_dotenv()
app = Flask(__name__)
app.secret_key = os.urandom(24)

# 데이터베이스 연결 함수
def get_db_connection():
    conn = psycopg2.connect(
        host=os.getenv('DB_HOST'),
        port=os.getenv('DB_PORT'),
        dbname=os.getenv('DB_NAME'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        sslmode='require' #Azure를 위해 반드시 추가
    )
    print('get_db_connection', conn)
    conn.autocommit = True
    return conn

@app.route('/')
def index():
    # 1. 데이터 베이스에 접속
    conn = get_db_connection()
    print('get_db_connection', conn)
    cursor = conn.cursor(cursor_factory=DictCursor)
    # 2. SELECT
    cursor.execute("SELECT id, title, author, created_at, view_count, like_count FROM board.posts ORDER BY created_at DESC")
    posts = cursor.fetchall()
    cursor.close()
    conn.close()
    # 3. index.html 파일에 변수로 넘겨주기
    return render_template('index.html', posts = posts)

@app.route('/create/', methods=['GET'] )
def create_form():
    return render_template('create.html')

@app.route('/create/',methods=['POST']  )
def create_post():
    #1. 폼에 있는 정보들을 get
    title = request.form.get('title')
    author = request.form.get('author')
    content = request.form.get('content')

    if not title or not author or not content:
        flash('모든 필드를 똑바로 채워주세요!!!!')
        return redirect(url_for('create_form'))
    
    # 1. 데이터 베이스에 접속
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=DictCursor)
    # 2. INSERT
    cursor.execute("INSERT INTO board.posts (title, author, content) VALUES (%s, %s, %s) RETURNING id", (title,author,content ))
    post_id = cursor.fetchone()[0]
    cursor.close()
    conn.close()
    flash('게시글이 성공적으로 등록되었음')
    return redirect(url_for('view_post', post_id=post_id))

@app.route('/post/<int:post_id>')
def view_post(post_id):
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=DictCursor)
    
    cursor.execute('UPDATE board.posts SET view_count = view_count + 1 WHERE id = %s', (post_id,))
    
    cursor.execute('SELECT * FROM board.posts WHERE id = %s', (post_id,))
    post = cursor.fetchone()
    
    if post is None:
        cursor.close()
        conn.close()
        flash('게시글을 찾을 수 없습니다.')
        return redirect(url_for('index'))
    
    cursor.execute('SELECT * FROM board.comments WHERE post_id = %s ORDER BY created_at', (post_id,))
    comments = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    user_ip = request.remote_addr
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM board.likes WHERE post_id = %s AND user_ip = %s', (post_id, user_ip))
    liked = cursor.fetchone()[0] > 0
    cursor.close()
    conn.close()
    
    return render_template('view.html', post=post, comments=comments, liked=liked)

@app.route('/edit/<int:post_id>', methods=['GET'])
def edit_form(post_id):
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=DictCursor)
    cursor.execute('SELECT * FROM board.posts WHERE id = %s', (post_id,))
    post = cursor.fetchone()
    cursor.close()
    conn.close()
    
    if post is None:
        flash('게시글을 찾을 수 없습니다.')
        return redirect(url_for('index'))
    
    return render_template('edit.html', post=post)

@app.route('/edit/<int:post_id>', methods=['POST'])
def edit_post(post_id):
    title = request.form.get('title')
    content = request.form.get('content')
    
    if not title or not content:
        flash('제목과 내용을 모두 입력해주세요.')
        return redirect(url_for('edit_form', post_id=post_id))
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        'UPDATE board.posts SET title = %s, content = %s, updated_at = %s WHERE id = %s',
        (title, content, datetime.now(), post_id)
    )
    cursor.close()
    conn.close()
    
    flash('게시글이 성공적으로 수정되었습니다.')
    return redirect(url_for('view_post', post_id=post_id))

@app.route('/delete/<int:post_id>', methods=['POST'])
def delete_post(post_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM board.posts WHERE id = %s', (post_id,))
    cursor.close()
    conn.close()
    
    flash('게시글이 성공적으로 삭제되었습니다.')
    return redirect(url_for('index'))

@app.route('/post/comment/<int:post_id>', methods=['POST'])
def add_comment(post_id):
    author = request.form.get('author')
    content = request.form.get('content')
    
    if not author or not content:
        flash('작성자와 내용을 모두 입력해주세요.')
        return redirect(url_for('view_post', post_id=post_id))
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        'INSERT INTO board.comments (post_id, author, content) VALUES (%s, %s, %s)',
        (post_id, author, content)
    )
    cursor.close()
    conn.close()
    
    flash('댓글이 등록되었습니다.')
    return redirect(url_for('view_post', post_id=post_id))

@app.route('/post/like/<int:post_id>', methods=['POST'])
def like_post(post_id):
    user_ip = request.remote_addr
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM board.likes WHERE post_id = %s AND user_ip = %s', (post_id, user_ip))
    already_liked = cursor.fetchone()[0] > 0
    
    if already_liked:
        cursor.execute('DELETE FROM board.likes WHERE post_id = %s AND user_ip = %s', (post_id, user_ip))
        cursor.execute('UPDATE board.posts SET like_count = like_count - 1 WHERE id = %s', (post_id,))
        message = '좋아요가 취소되었습니다.'
    else:
        cursor.execute('INSERT INTO board.likes (post_id, user_ip) VALUES (%s, %s)', (post_id, user_ip))
        cursor.execute('UPDATE board.posts SET like_count = like_count + 1 WHERE id = %s', (post_id,))
        message = '좋아요가 등록되었습니다.'
    
    cursor.close()
    conn.close()   
    flash(message)
    return redirect(url_for('view_post', post_id=post_id))


@app.route('/fms/result')
def fms_result():
    """total_result 뷰 데이터를 fms_result.html에 전달"""
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=DictCursor)
    cursor.execute("SELECT * FROM fms.total_result ORDER BY 도착일 DESC NULLS LAST")
    results = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('fms_result.html', results=results)


@app.route('/fms/analytics')
def fms_analytics():
    """FMS 데이터 기반 분석/시각화 페이지"""
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=DictCursor)

    # 1) 품종별 전체 마릿수
    cursor.execute(
        """
        SELECT 품종, COUNT(*) AS count
        FROM fms.total_result
        GROUP BY 품종
        ORDER BY count DESC
        """
    )
    breed_rows = cursor.fetchall()

    # 2) 품종별 Pass / Fail 분포
    cursor.execute(
        """
        SELECT 품종, 부적합여부, COUNT(*) AS count
        FROM fms.total_result
        GROUP BY 품종, 부적합여부
        ORDER BY 품종, 부적합여부
        """
    )
    pf_rows = cursor.fetchall()

    # 3) 날짜별 출하 마릿수
    cursor.execute(
        """
        SELECT 도착일, COUNT(*) AS count
        FROM fms.total_result
        GROUP BY 도착일
        ORDER BY 도착일
        """
    )
    daily_rows = cursor.fetchall()

    cursor.close()
    conn.close()

    # ---------- 파이 차트: 품종별 분포 ----------
    breed_labels = [row["품종"] for row in breed_rows]
    breed_values = [row["count"] for row in breed_rows]

    # ---------- 스택 막대: 품종별 Pass/Fail ----------
    breeds = sorted({row["품종"] for row in pf_rows})
    statuses = sorted({row["부적합여부"] for row in pf_rows})

    breed_index = {b: i for i, b in enumerate(breeds)}
    pf_data = {status: [0] * len(breeds) for status in statuses}

    for row in pf_rows:
        b = row["품종"]
        s = row["부적합여부"]
        pf_data[s][breed_index[b]] = row["count"]

    pastel_colors = [
        "#FFB5E8",
        "#B5DEFF",
        "#C7CEEA",
        "#E2F0CB",
        "#FFDAC1",
        "#FF9AA2",
        "#B5EAD7",
        "#E7FFAC",
    ]

    pf_datasets = []
    for i, status in enumerate(statuses):
        pf_datasets.append(
            {
                "label": status,
                "data": pf_data[status],
                "backgroundColor": pastel_colors[i % len(pastel_colors)],
                "borderWidth": 1,
            }
        )

    # ---------- 라인 차트: 날짜별 출하량 ----------
    daily_labels = [
        row["도착일"].strftime("%Y-%m-%d") if row["도착일"] else ""
        for row in daily_rows
    ]
    daily_values = [row["count"] for row in daily_rows]

    # 배송 지도 HTML 생성
    map_html = build_fms_map()

    return render_template(
        "fms_analytics.html",
        breed_labels=json.dumps(breed_labels, ensure_ascii=False),
        breed_values=json.dumps(breed_values),
        pf_labels=json.dumps(breeds, ensure_ascii=False),
        pf_datasets=json.dumps(pf_datasets, ensure_ascii=False),
        daily_labels=json.dumps(daily_labels, ensure_ascii=False),
        daily_values=json.dumps(daily_values),
        map_html=map_html,
    )


def build_fms_map():
    """고객사 / 도착지 기준 배송 현황 지도 생성 (folium HTML 반환)"""
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=DictCursor)

    # 고객사 / 도착지별 출하 건수
    cursor.execute(
        """
        SELECT 고객사, 도착지, COUNT(*) AS count
        FROM fms.total_result
        GROUP BY 고객사, 도착지
        ORDER BY count DESC
        """
    )
    rows = cursor.fetchall()

    cursor.close()
    conn.close()

    # 한국 주요 도시 좌표 (대략값)
    city_coords = {
        "서울": (37.5665, 126.9780),
        "인천": (37.4563, 126.7052),
        "부산": (35.1796, 129.0756),
        "대구": (35.8714, 128.6014),
        "광주": (35.1595, 126.8526),
        "대전": (36.3504, 127.3845),
        "울산": (35.5384, 129.3114),
        "세종": (36.4800, 127.2890),
        "수원": (37.2636, 127.0286),
        "창원": (35.2270, 128.6813),
        "청주": (36.6424, 127.4890),
        "전주": (35.8242, 127.1480),
        "포항": (36.0190, 129.3435),
        "제주": (33.4996, 126.5312),
    }

    # 기본 지도 (대한민국 중심, 귀여운 파스텔 톤 스타일)
    # tiles는 한국어 지도가 가능한 타일 서버를 ENV로 받을 수 있게 구성
    # 예: VWORLD, NAVER 등 -> .env에 KOREAN_TILE_URL 설정
    korean_tiles = os.getenv("KOREAN_TILE_URL")
    if korean_tiles:
        m = folium.Map(location=[36.5, 127.8], zoom_start=7, tiles=None, control_scale=True)
        folium.TileLayer(
            tiles=korean_tiles,
            attr="Korean map tiles",
            name="한국어 지도",
            overlay=False,
            control=False,
        ).add_to(m)
    else:
        # 기본 CartoDB 지도 (밝은 파스텔 톤)
        m = folium.Map(
            location=[36.5, 127.8],
            zoom_start=7,
            tiles="CartoDB positron",
            control_scale=True,
        )

    for row in rows:
        company = row["고객사"]
        city = row["도착지"]
        count = row["count"]

        if city not in city_coords:
            # 좌표가 정의되지 않은 도시는 스킵
            continue

        lat, lon = city_coords[city]

        # 출하 건수에 따라 마커 크기 조정 (최소 8, 최대 24 정도)
        radius = min(24, 8 + count * 0.7)

        popup_html = f"""
        <div style='font-size:13px;'>
          <b>고객사:</b> {company}<br>
          <b>도착지:</b> {city}<br>
          <b>출하 건수:</b> {count}건
        </div>
        """

        folium.CircleMarker(
            location=[lat, lon],
            radius=radius,
            popup=popup_html,
            color="#FFB5E8",  # 파스텔 핑크
            fill=True,
            fill_color="#B5EAD7",  # 파스텔 민트
            fill_opacity=0.8,
            weight=1.2,
        ).add_to(m)

    # folium 지도를 HTML로 렌더링하여 반환
    return m._repr_html_()


@app.route('/fms/map')
def fms_map():
    """고객사 / 도착지 기준 배송 현황 지도 시각화 (단독 페이지)"""
    map_html = build_fms_map()
    return render_template("fms_map.html", map_html=map_html)


if __name__ == '__main__':
    app.run(debug=True)

