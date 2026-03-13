import streamlit as st
import pandas as pd
import altair as alt

st.set_page_config(page_title="LPT 배치 스케줄러", page_icon="⚙️", layout="wide")

# Custom CSS for UI
st.markdown("""
<style>
    .main-title {
        color: #1565c0;
        text-align: center;
        font-size: 32px;
        font-weight: 800;
        margin-bottom: 20px;
    }
    .info-box {
        background-color: #e3f2fd;
        border: 2px solid #90caf9;
        padding: 15px;
        border-radius: 8px;
        margin-bottom: 20px;
        text-align: center;
        font-size: 15px;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-title">⚙️ LPT (Longest Processing Time) 배치 스케줄러</div>', unsafe_allow_html=True)
st.markdown("""
<div class="info-box">
LPT 알고리즘에 기반하여 여러 배치 작업을 5개(또는 지정된 개수)의 슬롯에 배분하여 <b>전체 종료 시간(Makespan)</b>을 최소화합니다.<br>
'수행시간'을 기준으로 내림차순 정렬(qsort) 후, 가장 빨리 비는 슬롯에 작업을 순차적으로 할당합니다.
</div>
""", unsafe_allow_html=True)

# Sidebar Settings
st.sidebar.header("🛠️ 스케줄러 설정")
num_slots = st.sidebar.number_input("슬롯 개수", min_value=1, value=5, step=1)

st.sidebar.markdown("---")
st.sidebar.subheader("🛡️ 예외 처리 (슬롯 제한 로직)")
enable_constraints = st.sidebar.checkbox("헤비/라이트 작업 제한 사용", value=False)

if enable_constraints:
    threshold = st.sidebar.number_input("헤비급 판단 기준 (수행시간 이상)", min_value=1, value=100)
    max_heavy = st.sidebar.number_input("슬롯당 최대 헤비급 작업 수", min_value=0, value=2)
    max_light = st.sidebar.number_input("슬롯당 최대 라이트급 작업 수", min_value=0, value=3)
    st.sidebar.caption("※ 제한 조건(예: 헤비급 2개+라이트급 3개)으로 인해 할당이 안 되는 작업이 생길 수 있습니다.")
else:
    threshold = 100
    max_heavy = 999
    max_light = 999

DEFAULT_INPUT = """1, 120
2, 45
3, 200
4, 80
5, 90
6, 150
7, 30
8, 10
9, 110
10, 60
11, 70
12, 130
13, 20
14, 55
15, 180
16, 95"""

st.subheader("📝 작업 데이터 입력")
st.caption("형식: [순번, 수행시간] (각 줄에 하나씩 입력)")
user_input = st.text_area("데이터 입력", value=DEFAULT_INPUT, height=200, label_visibility="collapsed")

if st.button("🚀 스케줄링 실행", use_container_width=True):
    # 입력 파싱
    jobs = []
    lines = user_input.strip().split('\n')
    for line in lines:
        parts = [p.strip() for p in line.split(',')]
        if len(parts) >= 2:
            job_id = parts[0]
            try:
                p_time = float(parts[1])
                jobs.append({'id': job_id, 'time': p_time})
            except ValueError:
                st.warning(f"수행 시간 형식 오류: {line}")
    
    if jobs:
        # 원래 순서 보존
        jobs_original = list(jobs)
        # LPT 정렬 (수행시간 내림차순)
        jobs.sort(key=lambda x: x['time'], reverse=True)
        
        # 슬롯 초기화
        slots = [{'id': i+1, 'total_time': 0.0, 'jobs': [], 'heavy_count': 0, 'light_count': 0} for i in range(num_slots)]
        unassigned_jobs = []
        
        # 작업 할당
        for job in jobs:
            is_heavy = job['time'] >= threshold
            
            # 할당 가능한 슬롯 필터링
            valid_slots = []
            for s in slots:
                if enable_constraints:
                    if is_heavy and s['heavy_count'] >= max_heavy:
                        continue
                    if not is_heavy and s['light_count'] >= max_light:
                        continue
                valid_slots.append(s)
            
            if not valid_slots:
                unassigned_jobs.append(job)
                continue
            
            # 가장 빨리 비는 곳(total_time이 가장 작은 슬롯) 찾기
            best_slot = min(valid_slots, key=lambda x: x['total_time'])
            
            # 작업 할당
            best_slot['jobs'].append({
                'id': job['id'], 
                'time': job['time'], 
                'type': 'Heavy' if is_heavy else 'Light'
            })
            best_slot['total_time'] += job['time']
            if is_heavy:
                best_slot['heavy_count'] += 1
            else:
                best_slot['light_count'] += 1

        # 전체 Makespan 계산
        makespan = max(s['total_time'] for s in slots)
        
        st.markdown("---")
        st.success(f"✅ 스케줄링 성공! **전체 배치 종료 시간(Makespan)은 {makespan}** 입니다.")
        
        # 시각화 데이터 준비
        chart_data = []
        for slot in slots:
            accumulated = 0
            for j in slot['jobs']:
                chart_data.append({
                    'Slot': f"Slot {slot['id']} (총: {slot['total_time']})",
                    'SlotID': slot['id'],
                    'Job': f"순번 {j['id']} ({j['time']})",
                    'JobID': j['id'],
                    'Start': accumulated,
                    'End': accumulated + j['time'],
                    'Time': j['time'],
                    'Type': j['type']
                })
                accumulated += j['time']
                
        # 간트 차트 (Altair Bar Chart 활용)
        if chart_data:
            df_chart = pd.DataFrame(chart_data)
            chart = alt.Chart(df_chart).mark_bar(stroke='white').encode(
                x=alt.X('Start:Q', title="실행 시간 흐름"),
                x2='End:Q',
                y=alt.Y('Slot:O', title="슬롯", sort=[f"Slot {i+1}" for i in range(num_slots)]),
                color=alt.Color('Job:N', legend=alt.Legend(title="작업 ID (시간)")),
                tooltip=['Slot', 'Job', 'Time', 'Type', 'Start', 'End']
            ).properties(
                height=300,
                title="LPT 배치 스케줄 간트 차트"
            ).interactive()
            
            st.altair_chart(chart, use_container_width=True)
            
        st.markdown("---")
        
        # 전체 실행 순서 비교 출력
        st.subheader("🔄 작업 실행 순서 비교 및 1:1 매핑")
        
        # 1. 기존 순서의 잡 ID 리스트
        original_ids = [j['id'] for j in jobs_original]
        
        # 2. 시작 시간(Start)과 먼저 비는 슬롯 번호 순으로 정렬한 변경 후 잡 ID 리스트
        sorted_by_start = sorted(chart_data, key=lambda x: (x['Start'], x['SlotID']))
        new_ids = [x['JobID'] for x in sorted_by_start]
        
        # 길이 맞추기 (미할당된 작업이 있을 수 있음)
        max_len = max(len(original_ids), len(new_ids))
        padded_original = original_ids + ['-'] * (max_len - len(original_ids))
        padded_new = new_ids + ['-'] * (max_len - len(new_ids))
        
        # 매핑 데이터프레임 생성
        mapping_df = pd.DataFrame({
            "실행 순번": [f"{i+1}번째" for i in range(max_len)],
            "기존 입력 기준 작업": padded_original,
            "LPT 스케줄링 후 작업": padded_new
        })
        
        # 화살표 문자열로 요약 
        original_order_str = " ➔ ".join(str(i) for i in original_ids)
        new_order_str = " ➔ ".join(str(i) for i in new_ids)
        
        st.markdown("**1:1 순서 매핑 테이블**")
        st.dataframe(mapping_df, hide_index=True, use_container_width=True)
        
        st.markdown("**기존 전체 순서**")
        st.info(original_order_str)
        st.markdown("**변경 전체 순서 (시작 시간 기준)**")
        st.success(new_order_str)

        st.markdown("---")

        # 슬롯별 표 데이터 출력
        st.subheader("📊 슬롯별 할당 결과")
        cols = st.columns(num_slots)
        for i, slot in enumerate(slots):
            with cols[i % num_slots]:
                st.markdown(f"**🟢 Slot {slot['id']}**")
                st.caption(f"총 시간: **{slot['total_time']}**")
                if enable_constraints:
                    st.caption(f"(Heavy: {slot['heavy_count']} / Light: {slot['light_count']})")
                
                if slot['jobs']:
                    df_slot = pd.DataFrame(slot['jobs'])
                    df_slot.columns = ['작업 순번', '수행시간', '구분']
                    st.dataframe(df_slot, hide_index=True)
                else:
                    st.info("할당된 작업 없음")

        # 할당 실패한 작업이 있을 경우
        if unassigned_jobs:
            st.error("⚠️ 슬롯 제한 규칙(Heavy/Light 개수 제한)으로 인해 할당되지 못한 작업이 있습니다.")
            df_unassigned = pd.DataFrame(unassigned_jobs)
            df_unassigned.columns = ['작업 순번', '수행시간']
            st.dataframe(df_unassigned, hide_index=True)
    else:
        st.error("입력된 데이터가 없습니다.")
