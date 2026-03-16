import streamlit as st
import pandas as pd
import altair as alt
import random

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

st.markdown('<div class="main-title">⚙️ 멀티 알고리즘 배치 스케줄러</div>', unsafe_allow_html=True)
st.markdown("""
<div class="info-box">
다양한 스케줄링 알고리즘을 선택하여 성능(Makespan 등)을 비교 분석할 수 있습니다.<br>
(기본 LPT, 단기작업 우선 SPT, 무작위 랜덤 등)
</div>
""", unsafe_allow_html=True)

# Sidebar Settings
st.sidebar.header("🛠️ 스케줄러 설정")
num_slots = st.sidebar.number_input("슬롯 개수", min_value=1, value=5, step=1)

st.sidebar.markdown("---")
st.sidebar.subheader("🧠 알고리즘 다중 선택")
st.sidebar.caption("※ 여러 개를 선택하여 성능(Makespan)을 한눈에 비교해보세요!")
algo_options = {
    # 기본 알고리즘군
    "Baseline": "1. 단순 도착 순서 (Baseline)",
    "LPT": "2. LPT (Longest Processing Time)",
    "SPT": "3. SPT (Shortest Processing Time)",
    "LPT_Constraint": "4. LPT + 헤비/라이트 예약 슬롯",
    "Random": "5. 무작위 할당 (Random)",
    
    # 고급 알고리즘군
    "LPT_LocalSearch": "6. [고급] LPT + Local Search",
    "LPT_Weighted": "7. [고급] Machine Speed (가중치)",
    "FFD_Target": "8. [고급] FFD (목표치 기반 포장)",
    "LPT_Chunking": "9. [고급] LPT + Chunking",
    "SA": "10. [고급] Simulated Annealing",
    
    # 균등/추가 알고리즘군 (Machine Speed 미적용)
    "LRFPT": "11. [균등] 동적 할당 (LRFPT)",
    "MULTIFIT": "12. [균등] 다중 포장 점근 (MULTIFIT)",
    "BFD": "13. [균등] 최소 빈틈 채우기 (BFD)",
    "RR_LPT": "14. [균등] 짝수/홀수 패키징 (Round-Robin)",
    "Tabu": "15. [균등] 금지 목록 탐색 (Tabu Search)"
}

# 다중 선택 (리스트로 반환됨)
selected_algo_keys = st.sidebar.multiselect(
    "비교할 알고리즘 선택",
    options=list(algo_options.keys()),
    default=["Baseline", "LPT", "SA"],
    format_func=lambda x: algo_options[x]
)

st.sidebar.markdown("---")
st.sidebar.subheader("⚙️ 알고리즘 세부 설정")

# 설정 변수들 초기화 (여러 알고리즘이 동시에 돌아가므로 공통으로 쓸 변수들 세팅)
enable_constraints = ("LPT_Constraint" in selected_algo_keys)
is_weighted_any = ("LPT_Weighted" in selected_algo_keys)
is_chunking_any = ("LPT_Chunking" in selected_algo_keys)

if enable_constraints:
    st.sidebar.markdown("**[LPT + 예약 슬롯용]**")
    threshold = st.sidebar.number_input("헤비급 기준 (수행시간 이상)", min_value=1.0, value=100.0, step=1.0)
    num_heavy_slots = st.sidebar.number_input("헤비급 우선 슬롯 개수", min_value=0, max_value=num_slots, value=min(num_slots, 4))
else:
    threshold = 100.0
    num_heavy_slots = num_slots

if is_chunking_any:
    st.sidebar.markdown("**[Chunking 용]**")
    chunk_threshold = st.sidebar.number_input("초소형 판단 기준", min_value=0.1, value=1.0, step=0.1)

DEFAULT_INPUT = """1, 5.1
2, 157.4
3, 189.8
4, 89.4
5, 48.5
6, 1.1
7, 0.9
8, 0.4
9, 0.7
10, 0.4
11, 0.4
12, 0.4
13, 0.5
14, 0.3
15, 0.4
16, 0.7
17, 0.3
18, 0.3
19, 0.3
20, 0.3
21, 0.6
22, 0.4
23, 0.3
24, 0.4
25, 0.3
26, 0.6
27, 0.6
28, 0.9
29, 0.4
30, 1
31, 0.5
32, 0.5
33, 0.5
34, 0.7
35, 0.4
36, 1.6
37, 0.7
38, 0.9
39, 1.1
40, 0.8
41, 0.4
42, 0.4
43, 0.6
44, 0.6
45, 0.8
46, 0.07
47, 0.6
48, 0.5
49, 1.1
50, 1
51, 1.1
52, 0.6
53, 1
54, 0.7
55, 1
56, 1.5
57, 0.6
58, 0.6
59, 0.5
60, 1.2
61, 0.9
62, 1
63, 0.6
64, 0.7
65, 1.1
66, 1.5
67, 1.6
68, 1.6
69, 1.1
70, 0.9
71, 1.5
72, 1.1
73, 2.1
74, 0.8
75, 1.8
76, 1.7
77, 0.9
78, 0.9
79, 1.8
80, 1.4
81, 1.5
82, 2.3
83, 2.3
84, 1.2
85, 2.2
86, 17
87, 1.6
88, 2.2
89, 1.3
90, 0.9
91, 3.1
92, 3.7
93, 17
94, 1.6
95, 2.3
96, 2.2
97, 2.1
98, 1.8
99, 3.1
100, 1
101, 2
102, 2.4
103, 1.8
104, 4
105, 2.6
106, 5.3
107, 4
108, 3.1
109, 3
110, 3.4
111, 6.4
112, 3.9
113, 3.8
114, 2.5
115, 2.3
116, 5.1
117, 4.9
118, 3.4
119, 3.7
120, 4.3
121, 3.7
122, 3.9
123, 4.3
124, 4.1
125, 6.2
126, 5.7
127, 14.1
128, 9.8
129, 11.5
130, 9.3
131, 31.2
132, 10.6
133, 16.5
134, 14.2
135, 20.4
136, 28.9
137, 20.2
138, 27.2
139, 19
140, 84
141, 24.6
"""

st.subheader("📝 작업 데이터 입력")
st.caption("형식: [순번, 수행시간] (각 줄에 하나씩 입력)")
user_input = st.text_area("데이터 입력", value=DEFAULT_INPUT, height=200, label_visibility="collapsed")

col_btn1, col_btn2 = st.columns([1, 1])
with col_btn1:
    btn_run = st.button("🚀 스케줄링 실행", use_container_width=True)
with col_btn2:
    btn_sim_range = st.button("📈 헤비/라이트 임계값 연속 시뮬레이션", use_container_width=True)

if btn_run or btn_sim_range:
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
        def allocate_jobs(job_list, apply_constraints=True, apply_weights=False, apply_ffd=False, current_threshold=100.0):
            alloc_slots = [{'id': i+1, 'total_time': 0.0, 'jobs': [], 'heavy_count': 0, 'light_count': 0, 'weight': 1.0} for i in range(num_slots)]
            
            # 머신 스피드(가중치) 부여 (시뮬레이션 용 랜덤)
            if apply_weights:
                for s in alloc_slots:
                    s['weight'] = random.uniform(0.8, 1.5)
            
            unassigned = []
            
            # FFD 용 사전 계산 (전체 평균 목표 시간)
            target_makespan = sum([j['time'] for j in job_list]) / num_slots if job_list else 0
            
            for job in job_list:
                is_heavy = job['time'] >= current_threshold
                valid_slots = []
                for idx, s in enumerate(alloc_slots):
                    if apply_constraints and enable_constraints:
                        is_heavy_slot = idx < num_heavy_slots
                        if is_heavy and not is_heavy_slot:
                            continue
                    valid_slots.append(s)
                if not valid_slots:
                    unassigned.append(job)
                    continue
                
                # FFD 로직: 앞에서부터 순서대로 보며 평균 목표치(target)를 넘지 않으면 무조건 삽입
                best_slot = None
                if apply_ffd:
                    for s in valid_slots:
                        if s['total_time'] + (job['time'] / s['weight']) <= target_makespan:
                            best_slot = s
                            break
                
                # FFD로 못 찾았거나, 다른 알고리즘인 경우 (최소 total_time 기준, 단 가중치 고려)
                if not best_slot:
                    best_slot = min(valid_slots, key=lambda x: x['total_time'] + (job['time'] / x['weight']))
                
                if apply_constraints and enable_constraints and not is_heavy:
                    # 라이트급 잡의 경우, 라이트 전용 슬롯이 완전히 비어있을 때만 우선 할당
                    empty_light_slots = [s for s in valid_slots if s['total_time'] == 0.0 and s['id'] - 1 >= num_heavy_slots]
                    if empty_light_slots:
                        best_slot = min(empty_light_slots, key=lambda x: x['total_time'])

                actual_time = job['time'] / best_slot['weight']  # 머신 속도 반영된 실제 수행시간
                
                best_slot['jobs'].append({
                    'id': job['id'], 
                    'time': actual_time, 
                    'original_time': job['time'],
                    'type': 'Heavy' if is_heavy else 'Light'
                })
                best_slot['total_time'] += actual_time
                if is_heavy:
                    best_slot['heavy_count'] += 1
                else:
                    best_slot['light_count'] += 1
            span = max([s['total_time'] for s in alloc_slots], default=0)
            return span, alloc_slots, unassigned

        # 1. 제약조건 없는 단순 Baseline 시간 먼저 구하기 (비교율 계산용)
        original_makespan, _, _ = allocate_jobs(jobs_original, apply_constraints=False)

        # 각 알고리즘별 결과를 담을 리스트
        results = []

        if not selected_algo_keys:
            st.warning("👈 좌측 사이드바에서 비교할 알고리즘을 하나 이상 선택해 주세요.")
            st.stop()
            
        # 선택된 모든 알고리즘 루프
        for algo_key in selected_algo_keys:
            process_jobs = list(jobs) # 독립적인 복사본 사용
            
            # 고급 알고리즘 전처리 단계
            if algo_key == "LPT_Chunking":
                small_jobs = [j for j in process_jobs if j['time'] < chunk_threshold]
                large_jobs = [j for j in process_jobs if j['time'] >= chunk_threshold]
                if small_jobs:
                    chunk_time = sum([j['time'] for j in small_jobs])
                    chunk_job = {'id': f"Chunk({len(small_jobs)})", 'time': chunk_time}
                    process_jobs = large_jobs + [chunk_job]
            elif algo_key == "RR_LPT":
                process_jobs.sort(key=lambda x: x['time'], reverse=True)
                paired_jobs = []
                n = len(process_jobs)
                for i in range(n // 2):
                    t = process_jobs[i]['time'] + process_jobs[n-1-i]['time']
                    paired_jobs.append({'id': f"P({process_jobs[i]['id']},{process_jobs[n-1-i]['id']})", 'time': t})
                if n % 2 != 0:
                    paired_jobs.append({'id': str(process_jobs[n//2]['id']), 'time': process_jobs[n//2]['time']})
                process_jobs = paired_jobs
            
            # 정렬 로직 (기본)
            if algo_key in ["LPT", "LPT_Constraint", "LPT_LocalSearch", "LPT_Weighted", "FFD_Target", "LPT_Chunking", "LRFPT", "MULTIFIT", "Tabu", "BFD", "RR_LPT"]:
                process_jobs.sort(key=lambda x: x['time'], reverse=True)
            elif algo_key == "SPT":
                process_jobs.sort(key=lambda x: x['time'], reverse=False)
            elif algo_key in ["Random", "SA"]:
                random.shuffle(process_jobs)
                
            # 초기 할당 (Allocate)
            is_weighted = (algo_key == "LPT_Weighted")
            is_ffd = (algo_key == "FFD_Target")
            if algo_key == "MULTIFIT":
                lower = max(max((j['time'] for j in process_jobs), default=0), sum(j['time'] for j in process_jobs)/num_slots)
                upper = sum(j['time'] for j in process_jobs)
                best_slots = [{'id': i+1, 'total_time': 0, 'jobs': [], 'heavy_count':0,'light_count':0} for i in range(num_slots)]
                for _ in range(20):
                    mid = (lower + upper) / 2
                    temp_slots = [{'id': i+1, 'total_time': 0, 'jobs': [], 'heavy_count':0,'light_count':0} for i in range(num_slots)]
                    success = True
                    for job in process_jobs:
                        placed = False
                        for s in temp_slots:
                            if s['total_time'] + job['time'] <= mid:
                                s['jobs'].append({'id': job['id'], 'time': job['time'], 'original_time': job['time'], 'type': 'Light'})
                                s['total_time'] += job['time']
                                placed = True
                                break
                        if not placed:
                            success = False
                            break
                    if success:
                        best_slots = temp_slots
                        upper = mid
                    else:
                        lower = mid
                slots = best_slots
                makespan = max((s['total_time'] for s in slots), default=0)
                unassigned_jobs = []
            elif algo_key == "BFD":
                target = sum(j['time'] for j in process_jobs) / num_slots
                slots = [{'id': i+1, 'total_time': 0, 'jobs': [], 'heavy_count':0, 'light_count':0} for i in range(num_slots)]
                for job in process_jobs:
                    # 빈 여유공간(target - 현재)이 작업크기보다 큰 슬롯들 중 남은 빈공간이 가장 꽉 들어맞는(작은) 곳을 선택
                    valid_slots = [s for s in slots if s['total_time'] + job['time'] <= target * 2.5] 
                    if valid_slots:
                        best_s = min(valid_slots, key=lambda x: target - (x['total_time'] + job['time']) if target >= x['total_time'] + job['time'] else 99999)
                        # 만약 target 초과만 있다면 그냥 제일 덜 찬 곳
                        if target < (best_s['total_time'] + job['time']): 
                            best_s = min(slots, key=lambda x: x['total_time'])
                    else:
                        best_s = min(slots, key=lambda x: x['total_time'])
                    best_s['jobs'].append({'id': job['id'], 'time': job['time'], 'original_time': job['time'], 'type': 'Light'})
                    best_s['total_time'] += job['time']
                makespan = max(s['total_time'] for s in slots)
                unassigned_jobs = []
            else:
                makespan, slots, unassigned_jobs = allocate_jobs(
                    process_jobs, 
                    apply_constraints=(algo_key == "LPT_Constraint"),
                    apply_weights=is_weighted,
                    apply_ffd=is_ffd,
                    current_threshold=threshold
                )

            # 고급 알고리즘 후처리(Post-Optimization)
            if algo_key == "LPT_LocalSearch" and num_slots > 1:
                for _ in range(100): 
                    max_slot = max(slots, key=lambda x: x['total_time'])
                    min_slot = min(slots, key=lambda x: x['total_time'])
                    if max_slot == min_slot or not max_slot['jobs']: break
                    improved = False
                    for j_max in list(max_slot['jobs']):
                        min_jobs = list(min_slot['jobs']) if min_slot['jobs'] else [{'time': 0, 'id': None, 'original_time':0, 'type':''}]
                        for j_min in min_jobs:
                            diff = j_max['time'] - j_min['time']
                            if 0 < diff < (max_slot['total_time'] - min_slot['total_time']) / 2:
                                max_slot['jobs'].remove(j_max)
                                if j_min['id'] is not None:
                                    min_slot['jobs'].remove(j_min)
                                    max_slot['jobs'].append(j_min)
                                min_slot['jobs'].append(j_max)
                                max_slot['total_time'] -= diff
                                min_slot['total_time'] += diff
                                improved = True
                                break
                        if improved: break
                    if not improved: break
                makespan = max(s['total_time'] for s in slots)

            if algo_key == "SA" and num_slots > 1:
                temperature = 100.0
                cooling_rate = 0.95
                for _ in range(200): 
                    if temperature < 1.0: break
                    idx1 = random.randint(0, num_slots-1)
                    idx2 = random.randint(0, num_slots-1)
                    if idx1 == idx2 or not slots[idx1]['jobs']: continue
                    
                    job_to_move = random.choice(slots[idx1]['jobs'])
                    current_max = max(s['total_time'] for s in slots)
                    new_max1 = slots[idx1]['total_time'] - job_to_move['time']
                    new_max2 = slots[idx2]['total_time'] + job_to_move['time']
                    temp_max = max((new_max1, new_max2) + tuple(s['total_time'] for i,s in enumerate(slots) if i not in (idx1,idx2)))
                    
                    delta = temp_max - current_max
                    import math
                    if delta < 0 or random.random() < math.exp(-delta / temperature):
                        slots[idx1]['jobs'].remove(job_to_move)
                        slots[idx2]['jobs'].append(job_to_move)
                        slots[idx1]['total_time'] -= job_to_move['time']
                        slots[idx2]['total_time'] += job_to_move['time']
                        makespan = max(s['total_time'] for s in slots)
                    temperature *= cooling_rate

            if algo_key == "Tabu" and num_slots > 1:
                tabu_list = []
                tabu_tenure = 7
                best_makespan = makespan
                for _ in range(150): 
                    best_move = None
                    best_move_delta = float('inf')
                    for _ in range(30): 
                        idx1, idx2 = random.sample(range(num_slots), 2)
                        if not slots[idx1]['jobs'] or not slots[idx2]['jobs']: continue
                        j1 = random.choice(slots[idx1]['jobs'])
                        j2 = random.choice(slots[idx2]['jobs'])
                        
                        curr_max = max(s['total_time'] for s in slots)
                        n1 = slots[idx1]['total_time'] - j1['time'] + j2['time']
                        n2 = slots[idx2]['total_time'] - j2['time'] + j1['time']
                        temp_max = max((n1, n2) + tuple(s['total_time'] for i,s in enumerate(slots) if i not in (idx1,idx2)))
                        delta = temp_max - curr_max
                        
                        move_sig = tuple(sorted([str(j1['id']), str(j2['id'])]))
                        if move_sig not in tabu_list or temp_max < best_makespan:
                            if delta < best_move_delta:
                                best_move_delta = delta
                                best_move = (idx1, idx2, j1, j2, move_sig, temp_max)
                    
                    if best_move:
                        idx1, idx2, j1, j2, move_sig, temp_max = best_move
                        slots[idx1]['jobs'].remove(j1)
                        slots[idx1]['jobs'].append(j2)
                        slots[idx2]['jobs'].remove(j2)
                        slots[idx2]['jobs'].append(j1)
                        slots[idx1]['total_time'] += (j2['time'] - j1['time'])
                        slots[idx2]['total_time'] += (j1['time'] - j2['time'])
                        
                        tabu_list.append(move_sig)
                        if len(tabu_list) > tabu_tenure: tabu_list.pop(0)
                        
                        makespan = max(s['total_time'] for s in slots)
                        if makespan < best_makespan: best_makespan = makespan
                    
            # 해당 알고리즘 순회 완료, 결과 저장
            improvement_time = original_makespan - makespan
            improvement_rate = (improvement_time / original_makespan * 100) if original_makespan > 0 else 0
            
            # 새 ID 리스트 추출 (매핑용)
            chart_data_temp = []
            for slot in slots:
                acc = 0
                for j in slot['jobs']:
                    chart_data_temp.append({'Start': acc, 'SlotID': slot['id'], 'JobID': j['id']})
                    acc += j['time']
            sorted_by_start = sorted(chart_data_temp, key=lambda x: (x['Start'], x['SlotID']))
            new_ids = [x['JobID'] for x in sorted_by_start]
            
            # 이름 정리 (예: "10. [고급] SA" -> "[고급] SA")
            raw_name = algo_options[algo_key]
            short_name = raw_name.split(". ")[1] if ". " in raw_name else raw_name
            
            results.append({
                'Algorithm': short_name, # 번호 떼고 이름만
                'Key': algo_key,
                'Makespan': round(makespan, 2),
                '단축 시간': round(improvement_time, 2),
                '단축률(%)': round(improvement_rate, 2),
                'Slots': slots,         # 상세 데이터 보존
                'Unassigned': unassigned_jobs,
                'NewIDs': new_ids
            })

        st.success(f"✅ {len(selected_algo_keys)}개 알고리즘 스케줄링 동시 완료!")
        
        # ----------------------------------------------------
        # 1. 종합 비교 대시보드 (Bar Chart & Table)
        # ----------------------------------------------------
        st.markdown("## 🏆 다중 알고리즘 성능 비교 대시보드")
        
        # 결과를 Makespan 오름차순(가장 짧은게 1등)으로 정렬
        results_df = pd.DataFrame(results).sort_values(by='Makespan').reset_index(drop=True)
        results_df.index = results_df.index + 1 # 1등부터 시작
        
        col_chart, col_table = st.columns([1, 1])
        
        with col_chart:
            bar_chart = alt.Chart(results_df).mark_bar().encode(
                x=alt.X('Makespan:Q', title="전체 종료 시간 (Makespan, 짧을수록 좋음)"),
                y=alt.Y('Algorithm:N', sort='-x', title="적용 알고리즘"),
                color=alt.condition(
                    alt.datum.Makespan == results_df['Makespan'].min(),
                    alt.value('#FF4B4B'),     # 1등은 빨간색 강조
                    alt.value('#1f77b4')      # 나머지는 파란색
                ),
                tooltip=['Algorithm', 'Makespan', '단축률(%)']
            ).properties(height=250, title="Makespan 비교 차트")
            
            # 막대 옆에 값 표시
            text = bar_chart.mark_text(
                align='left', baseline='middle', dx=3
            ).encode(text='Makespan:Q')
            
            st.altair_chart(bar_chart + text, use_container_width=True)
            
        with col_table:
            st.markdown("#### 🥇 알고리즘별 성능 순위표")
            display_df = results_df[['Algorithm', 'Makespan', '단축 시간', '단축률(%)']]
            display_df.index.name = "순위"
            st.dataframe(display_df, use_container_width=True)
            
            best_algo = results_df.iloc[0]['Algorithm']
            st.info(f"💡 현재 데이터에서는 **{best_algo}** 방식이 전체 시간을 가장 크게 단축시켰습니다!")

        st.markdown("---")
        
        # ----------------------------------------------------
        # 2. 개별 알고리즘 상세 결과 (Tabs)
        # ----------------------------------------------------
        st.markdown("## 📊 개별 알고리즘 상세 간트 차트 및 슬롯 정보")
        
        # 선택된 알고리즘 탭 만들기 (순위 순으로)
        tabs = st.tabs([f"{idx+1}위: {row.Algorithm}" for idx, row in enumerate(results_df.itertuples())])
        
        original_ids = [j['id'] for j in jobs_original]
        
        for idx, row in enumerate(results_df.itertuples()):
            # getattr를 사용하여 NamedTuple 속성에 접근  
            with tabs[idx]:
                key = row.Key
                algo_name = row.Algorithm
                slots = row.Slots
                unassigned_jobs = row.Unassigned
                new_ids = row.NewIDs
                is_weighted = (key == "LPT_Weighted")
        
                chart_data = []
                for slot in slots:
                    accumulated = 0
                    for j in slot['jobs']:
                        weight_info = f" (속도:{slot['weight']:.2f}배)" if is_weighted else ""
                        chart_data.append({
                            'Slot': f"Slot {slot['id']}{weight_info} (총: {slot['total_time']:.2f})",
                            'SlotID': slot['id'],
                            'Job': f"순번 {j['id']} (원래:{j['original_time']:.2f} ➔ 적용:{j['time']:.2f})",
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
                        height=250,
                        title=f"{algo_name} 상세 간트 차트"
                    ).interactive()
                    
                    st.altair_chart(chart, use_container_width=True)
                    
                # 화살표 문자열로 요약 
                original_order_str = " ➔ ".join(str(i) for i in original_ids)
                new_order_str = " ➔ ".join(str(i) for i in new_ids)
                
                max_len = max(len(original_ids), len(new_ids))
                padded_original = original_ids + ['-'] * (max_len - len(original_ids))
                padded_new = new_ids + ['-'] * (max_len - len(new_ids))
                
                mapping_df = pd.DataFrame({
                    "실행 순번": [f"{i+1}번째" for i in range(max_len)],
                    "기존 입력 기준 작업": padded_original,
                    "적용 후 변경된 작업": padded_new
                })
                
                with st.expander(f"🔄 {algo_name} 실행 순서 매핑 테이블 보기"):
                    st.dataframe(mapping_df, hide_index=True, use_container_width=True)
                    st.markdown("**기존** : " + original_order_str)
                    st.markdown("**변경** : " + new_order_str)

                # 슬롯별 표 데이터 출력
                st.markdown(f"**🟢 {algo_name} 슬롯별 할당 결과**")
                cols = st.columns(num_slots)
                for i, slot in enumerate(slots):
                    with cols[i % num_slots]:
                        st.caption(f"Slot {slot['id']} / **{slot['total_time']:.2f}**")
                        if enable_constraints and key == "LPT_Constraint":
                            slot_type = "헤비급" if i < num_heavy_slots else "라이트"
                            st.caption(f"[{slot_type}] (H:{slot['heavy_count']}/L:{slot['light_count']})")
                        
                        if is_weighted:
                            st.caption(f"성능: {slot['weight']:.2f}배")
                        
                        if slot['jobs']:
                            df_slot = pd.DataFrame(slot['jobs'])
                            if is_weighted:
                                df_slot.columns = ['순번', '할당', '원래', '구분']
                                df_slot['할당'] = df_slot['할당'].apply(lambda x: f"{x:.2f}")
                                df_slot['원래'] = df_slot['원래'].apply(lambda x: f"{x:.2f}")
                            else:
                                df_slot.columns = ['순번', '수행시간', '원래', '구분']
                                df_slot = df_slot.drop('원래', axis=1)
                                
                            st.dataframe(df_slot, hide_index=True)

                if unassigned_jobs and key == "LPT_Constraint":
                    st.error("⚠️ 슬롯 제한 규칙 등으로 인해 할당 안 됨")
                    df_u = pd.DataFrame(unassigned_jobs)
                    df_u.columns = ['순번', '시간']
                    st.dataframe(df_u, hide_index=True)

        if btn_sim_range:
            st.markdown("---")
            st.markdown("## 📈 임계값(Threshold) 연속 시뮬레이션 결과")
            if not enable_constraints or "LPT_Constraint" not in selected_algo_keys:
                st.warning("이 기능을 사용하려면 좌측 사이드바에서 **'헤비/라이트 스케줄링 규칙 적용'**을 켜고, 알고리즘 선택에서 **'4. [기본] LPT + 헤비/라이트 (예약슬롯)'**을 하나 이상 선택해야 합니다.")
            else:
                min_time = min(j['time'] for j in jobs_original)
                max_time = max(j['time'] for j in jobs_original)
                
                sim_results = []
                # 1분(또는 입력 데이터의 시간 단위) 단위로 임계값 변경하며 테스트
                test_thresholds = [i for i in range(int(min_time), int(max_time) + 2)]
                
                progress_bar = st.progress(0)
                for idx, t_val in enumerate(test_thresholds):
                    test_jobs = list(jobs_original)
                    test_jobs.sort(key=lambda x: x['time'], reverse=True)
                    m_span, _, _ = allocate_jobs(test_jobs, apply_constraints=True, current_threshold=t_val)
                    
                    sim_results.append({'Threshold': t_val, 'Makespan': m_span})
                    progress_bar.progress((idx + 1) / len(test_thresholds))
                    
                df_sim = pd.DataFrame(sim_results)
                
                best_t = df_sim.loc[df_sim['Makespan'].idxmin()]['Threshold']
                min_m = df_sim['Makespan'].min()
                
                st.success(f"시뮬레이션 완료! 최적의 임계값은 **{best_t}** (Makespan: {min_m:.2f}) 입니다.")
                
                line_chart = alt.Chart(df_sim).mark_line(point=True).encode(
                    x=alt.X('Threshold:Q', title="헤비급 판단 임계값 (Threshold)"),
                    y=alt.Y('Makespan:Q', title="전체 소요 시간 (Makespan)", scale=alt.Scale(zero=False)),
                    tooltip=['Threshold', 'Makespan']
                ).properties(height=350, title="임계값 변화에 따른 소요 시간 비교")
                
                st.altair_chart(line_chart, use_container_width=True)
                
                # 원래 threshold 값 복구
                threshold = st.session_state.get('sidebar_threshold_val', threshold)

    else:
        st.error("입력된 데이터가 없습니다.")

# Streamlit 재실행 방어용 전역변수 백업
st.session_state['sidebar_threshold_val'] = threshold
