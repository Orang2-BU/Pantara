import { useEffect, useMemo, useState } from 'react';
import {
  Bell, BriefcaseBusiness, CheckCircle2, ChevronRight, CircleAlert, FolderKanban,
  Gauge, LayoutDashboard, Plus, RefreshCw, Settings, Users, X
} from 'lucide-react';

const API = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';
const nav = [
  ['dashboard', 'Dashboard', LayoutDashboard],
  ['projects', 'Projects', FolderKanban],
  ['team', 'My Team', Users],
  ['my-work', 'My Work', BriefcaseBusiness],
];

const list = async (path) => {
  const response = await fetch(`${API}/${path}/`);
  if (!response.ok) throw new Error(`${path}: ${response.status}`);
  const data = await response.json();
  return Array.isArray(data) ? data : data.results || [];
};

const initials = (name = '') => name.split(' ').map((word) => word[0]).join('').slice(0, 2).toUpperCase();
const titleize = (value = '') => value.replaceAll('_', ' ').replace(/\b\w/g, (letter) => letter.toUpperCase());
const statusClass = (status = '') => `status status-${status.toLowerCase().replaceAll('_', '-')}`;
const candidateReason = (candidate) => candidate?.recommendation_result?.reason_codes?.map(titleize).join(' · ') || 'Evidence sedang diproses';

function App() {
  const [page, setPage] = useState('dashboard');
  const [data, setData] = useState({ projects: [], tasks: [], members: [], assignments: [], blockers: [], analyses: [] });
  const [state, setState] = useState({ loading: true, error: '' });
  const [selectedTask, setSelectedTask] = useState(null);
  const [showTaskForm, setShowTaskForm] = useState(false);

  const load = async () => {
    setState({ loading: true, error: '' });
    try {
      const [projects, tasks, members, assignments, blockers, analyses] = await Promise.all(
        ['projects', 'tasks', 'members', 'assignments', 'blockers', 'adaptive-analyses'].map(list)
      );
      setData({ projects, tasks, members, assignments, blockers, analyses });
    } catch (error) {
      setState({ loading: false, error: 'Tidak dapat memuat data Pantara. Pastikan backend berjalan di localhost:8000.' });
      return;
    }
    setState({ loading: false, error: '' });
  };

  useEffect(() => { load(); }, []);
  const analysisByTask = useMemo(() => Object.fromEntries(data.analyses.map((item) => [item.task, item])), [data.analyses]);
  const openTasks = data.tasks.filter((task) => task.status !== 'COMPLETED');
  const activeBlockers = data.blockers.filter((blocker) => blocker.status !== 'RESOLVED');
  const chooseTask = (task) => { setSelectedTask(task); setPage('projects'); };

  const content = state.loading ? <Loading /> : state.error ? <Empty icon={CircleAlert} title="Backend belum terhubung" detail={state.error} action={<button className="button" onClick={load}>Coba lagi</button>} /> : {
    dashboard: <Dashboard tasks={openTasks} members={data.members} blockers={activeBlockers} analyses={analysisByTask} onChoose={chooseTask} />,
    projects: <Projects projects={data.projects} tasks={data.tasks} analysisByTask={analysisByTask} selectedTask={selectedTask} onChoose={setSelectedTask} onNew={() => setShowTaskForm(true)} />,
    team: <Team members={data.members} tasks={openTasks} />,
    'my-work': <MyWork assignments={data.assignments} tasks={data.tasks} members={data.members} analyses={analysisByTask} onReload={load} />,
    notifications: <Notifications blockers={activeBlockers} tasks={openTasks} analyses={analysisByTask} onChoose={chooseTask} />,
    settings: <SettingsPage />,
  }[page];

  return <div className="app-shell">
    <aside className="sidebar" aria-label="Navigasi utama">
      <button className="brand" onClick={() => setPage('dashboard')} aria-label="Pantara dashboard"><span className="brand-mark">P</span><span>Pantara</span></button>
      <nav>{nav.map(([id, label, Icon]) => <button key={id} className={page === id ? 'nav-item active' : 'nav-item'} onClick={() => setPage(id)}><Icon size={20} /><span>{label}</span></button>)}</nav>
      <div className="sidebar-bottom">
        <button className={page === 'notifications' ? 'nav-item active' : 'nav-item'} onClick={() => setPage('notifications')}><Bell size={20} /><span>Notifications</span>{activeBlockers.length > 0 && <b>{activeBlockers.length}</b>}</button>
        <button className={page === 'settings' ? 'nav-item active' : 'nav-item'} onClick={() => setPage('settings')}><Settings size={20} /><span>Settings</span></button>
      </div>
    </aside>
    <main className="main"><header className="topbar"><p>Human-centered workload workspace</p><button className="icon-button" onClick={load} aria-label="Refresh data"><RefreshCw size={18} /></button></header>{content}</main>
    {showTaskForm && <TaskForm projects={data.projects} onClose={() => setShowTaskForm(false)} onSaved={() => { setShowTaskForm(false); load(); }} />}
  </div>;
}

function PageHeader({ eyebrow, title, detail, action }) { return <section className="hero"><div><p className="eyebrow">{eyebrow}</p><h1>{title}</h1><p>{detail}</p></div>{action}</section>; }
function Loading() { return <div className="loading"><RefreshCw className="spin" /> Memuat workspace…</div>; }
function Empty({ icon: Icon, title, detail, action }) { return <div className="empty"><Icon size={34} /><h2>{title}</h2><p>{detail}</p>{action}</div>; }
function Metric({ icon: Icon, label, value, detail, tone = '' }) { return <article className={`metric ${tone}`}><Icon size={20} /><p>{label}</p><strong>{value}</strong><span>{detail}</span></article>; }

function Dashboard({ tasks, members, blockers, analyses, onChoose }) {
  const reviewed = tasks.filter((task) => analyses[task.id]?.recommendation?.review_candidates?.length).length;
  return <div className="page"><PageHeader eyebrow="Team lead workspace" title="Good morning, lead." detail="Lihat beban kerja, keputusan yang perlu ditinjau, dan tugas yang membutuhkan perhatian." action={<button className="button" onClick={() => window.scrollTo({ top: document.body.scrollHeight, behavior: 'smooth' })}>Review workload <ChevronRight size={16} /></button>} />
    <section className="metrics"><Metric icon={BriefcaseBusiness} label="Open tasks" value={tasks.length} detail="Belum selesai" /><Metric icon={Users} label="Team members" value={members.length} detail="Dalam workspace" tone="accent" /><Metric icon={CircleAlert} label="Active blockers" value={blockers.length} detail="Memerlukan tindak lanjut" tone={blockers.length ? 'warning' : ''} /><Metric icon={Gauge} label="Review needed" value={reviewed} detail="Keputusan tidak otomatis" tone="accent" /></section>
    <section className="section-head"><div><h2>Workload review</h2><p>Prioritas berdasarkan kondisi tugas terbaru, bukan ranking karyawan.</p></div></section>
    <div className="work-list">{tasks.slice(0, 5).map((task) => <TaskRow key={task.id} task={task} analysis={analyses[task.id]} onClick={() => onChoose(task)} />)}{!tasks.length && <Empty icon={CheckCircle2} title="Tidak ada tugas terbuka" detail="Buat proyek dan task pertama untuk memulai analisis." />}</div>
  </div>;
}

function TaskRow({ task, analysis, onClick }) { const recommendation = analysis?.recommendation; const name = recommendation?.recommended_member_name || 'Human review required'; return <button className="task-row" onClick={onClick}><span className="task-icon"><BriefcaseBusiness size={20} /></span><span className="task-copy"><strong>{task.title}</strong><small>{task.estimated_effort} jam · {titleize(task.complexity)} complexity</small></span><span className="task-decision"><small>{recommendation?.recommended_member_id ? 'Recommended' : 'Needs review'}</small><strong>{name}</strong></span><ChevronRight size={20} /></button>; }

function Projects({ projects, tasks, analysisByTask, selectedTask, onChoose, onNew }) {
  const task = selectedTask || tasks[0];
  return <div className="page"><PageHeader eyebrow="Engineering portfolio" title="Projects & task decisions" detail="Buat task, lihat dampak workload, lalu putuskan assignment secara manusiawi." action={<button className="button" onClick={onNew}><Plus size={17} /> New task</button>} />
    <div className="project-grid">{projects.map((project) => { const projectTasks = tasks.filter((item) => item.project === project.id); const progress = projectTasks.length ? Math.round(projectTasks.reduce((total, item) => total + item.progress, 0) / projectTasks.length) : 0; return <article key={project.id} className="project-card"><span className="status status-pending">{projectTasks.length} tasks</span><h2>{project.name}</h2><p>Deadline {project.deadline || 'belum ditentukan'}</p><div className="progress"><i style={{ width: `${progress}%` }} /></div><small>{progress}% task progress</small></article>; })}</div>
    <section className="split"><div><div className="section-head"><div><h2>Task queue</h2><p>Pilih task untuk membuka decision brief.</p></div></div><div className="work-list">{tasks.map((item) => <TaskRow key={item.id} task={item} analysis={analysisByTask[item.id]} onClick={() => onChoose(item)} />)}</div></div><AnalysisPanel task={task} analysis={task && analysisByTask[task.id]} /></section>
  </div>;
}

function AnalysisPanel({ task, analysis }) {
  if (!task) return <aside className="analysis-panel"><Empty icon={FolderKanban} title="Pilih sebuah task" detail="Decision brief akan muncul di sini." /></aside>;
  const candidates = analysis?.candidates || []; const recommendation = analysis?.recommendation || {};
  return <aside className="analysis-panel"><p className="eyebrow">Adaptive decision brief</p><h2>{task.title}</h2><p className="muted">{task.description || `${task.estimated_effort} jam · ${titleize(task.complexity)}`}</p><div className="reason-box"><strong>{recommendation.recommended_member_name || 'Human review required'}</strong><p>{recommendation.reason || 'Analisis belum tersedia. Jalankan endpoint Analyze Team untuk task ini.'}</p>{(recommendation.reason_codes || []).map((reason) => <span className="chip" key={reason}>{titleize(reason)}</span>)}</div><h3>Candidates</h3>{candidates.slice(0, 4).map((candidate) => <article className="candidate" key={candidate.member_id}><div><strong>{candidate.member_name}</strong><small>{candidateReason(candidate)}</small></div><span className={statusClass(candidate.recommendation_result?.recommendation)}>{titleize(candidate.recommendation_result?.recommendation || 'unknown')}</span></article>)}</aside>;
}

function Team({ members, tasks }) { return <div className="page"><PageHeader eyebrow="Engineering pod" title="My team" detail="Beban kerja adalah konteks assignment, bukan pengukuran performa." /><div className="team-grid">{members.map((member) => { const owned = tasks.filter((task) => task.assignments?.some((assignment) => assignment.member === member.id)); return <article className="member-card" key={member.id}><span className="avatar">{initials(member.name)}</span><h2>{member.name}</h2><p>{titleize(member.role)}</p><span className={statusClass(member.latest_capacity_signal || 'balanced')}>{titleize(member.latest_capacity_signal || 'balanced')}</span><dl><div><dt>Open work</dt><dd>{owned.length} tasks</dd></div><div><dt>Skills</dt><dd>{member.work_profile?.skills?.length || 0} listed</dd></div></dl></article>; })}</div></div>; }
function MyWork({ assignments, tasks, members, analyses, onReload }) {
  const [mode, setMode] = useState('');
  const worker = members.find((member) => member.role === 'EMPLOYEE') || members[0];
  const mine = assignments.filter((assignment) => assignment.member === worker?.id).map((assignment) => ({ assignment, task: tasks.find((task) => task.id === assignment.task) })).filter(({ task }) => task);
  const suggestions = tasks.map((task) => ({ task, candidate: analyses[task.id]?.candidates?.find((candidate) => candidate.member_id === worker?.id) })).filter(({ candidate }) => ['RECOMMENDED', 'ALTERNATIVE'].includes(candidate?.recommendation_result?.recommendation));
  const capacity = { AVAILABLE: 40, BALANCED: 60, NEAR_CAPACITY: 78, OVER_CAPACITY: 92 }[worker?.latest_capacity_signal] || 60;
  const completed = tasks.filter((task) => task.status === 'COMPLETED').length;
  if (!worker) return <div className="page"><Empty icon={Users} title="Belum ada anggota tim" detail="Tambahkan worker untuk melihat personal workspace." /></div>;
  return <div className="page worker-page"><PageHeader eyebrow="Personal workspace" title={`Halo, ${worker.name.split(' ')[0]}.`} detail="Lihat beban kerja, alasan rekomendasi, dan update kondisi kerja Anda." action={<div className="hero-actions"><button className="button secondary" onClick={() => setMode('capacity')}>Update status</button><button className="button" onClick={() => setMode('progress')}>Log waktu</button></div>} />
    <section className="metrics worker-metrics"><Metric icon={Gauge} label="Kapasitas saya" value={`${capacity}%`} detail={`${titleize(worker.latest_capacity_signal || 'balanced')} — Anda dapat memperbarui sinyal ini kapan saja.`} /><Metric icon={CheckCircle2} label="Selesai" value={completed} detail="Task selesai di workspace ini" tone="accent" /></section>
    <section className="section-head"><div><h2>Rekomendasi tugas</h2><p>Disarankan dari skill, kapasitas, access readiness, dan evidence yang dapat dilihat.</p></div></section>
    <div className="worker-recommendations">{suggestions.map(({ task, candidate }) => <WorkerSuggestion key={task.id} task={task} candidate={candidate} />)}{!suggestions.length && <Empty icon={BriefcaseBusiness} title="Belum ada rekomendasi baru" detail="Rekomendasi muncul setelah team lead menjalankan analisis task." />}</div>
    <section className="section-head"><div><h2>Task saya</h2><p>Assignment selalu diputuskan manusia; update progress menjaga analisis tetap relevan.</p></div></section>
    <div className="work-list">{mine.map(({ assignment, task }) => <article className="assignment" key={assignment.id}><span className="avatar small">{initials(worker.name)}</span><div><strong>{task.title}</strong><p>{assignment.reason || 'Assignment team lead'} · {task.progress}% complete</p></div><span className={statusClass(task.status)}>{titleize(task.status)}</span></article>)}{!mine.length && <Empty icon={BriefcaseBusiness} title="Belum ada task yang ditugaskan" detail="Tidak ada assignment otomatis. Team lead akan mengonfirmasi tugas yang dipilih." />}</div>
    {mode === 'capacity' && <CapacityForm worker={worker} onClose={() => setMode('')} onSaved={() => { setMode(''); onReload(); }} />}{mode === 'progress' && <ProgressForm assignments={mine} onClose={() => setMode('')} onSaved={() => { setMode(''); onReload(); }} />}
  </div>;
}

function WorkerSuggestion({ task, candidate }) { const [open, setOpen] = useState(false); const capacity = candidate.capacity || {}; return <article className="worker-suggestion"><button className="suggestion-main" onClick={() => setOpen(!open)}><span className="task-icon"><BriefcaseBusiness size={20} /></span><span><strong>{task.title}</strong><p>{candidateReason(candidate)}</p></span><span className={statusClass(candidate.recommendation_result?.recommendation)}>{titleize(candidate.recommendation_result?.recommendation)}</span><ChevronRight className={open ? 'rotate' : ''} size={18} /></button>{open && <div className="suggestion-detail"><p><b>Why this task?</b> {candidate.recommendation_result?.considerations?.join(' ') || 'Kondisi capability, capacity, dan access saat ini mendukung untuk dipertimbangkan.'}</p><div><span className="chip">Current: {titleize(capacity.current_fit || 'unknown')}</span><span className="chip">Projected: {titleize(capacity.fit || 'unknown')}</span><span className="chip">{task.estimated_effort} hours</span></div><small>Task ini belum di-assign otomatis. Diskusikan dengan team lead jika Anda ingin mengambilnya.</small></div>}</article>; }

function CapacityForm({ worker, onClose, onSaved }) { const [error, setError] = useState(''); const [saving, setSaving] = useState(false); const submit = async (event) => { event.preventDefault(); setSaving(true); const level = new FormData(event.currentTarget).get('level'); try { const response = await fetch(`${API}/members/${worker.id}/capacity/`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ level, context: [] }) }); if (!response.ok) throw new Error('Status tidak dapat diperbarui.'); onSaved(); } catch (reason) { setError(reason.message); } setSaving(false); }; return <div className="modal-backdrop" role="dialog" aria-modal="true"><form className="modal" onSubmit={submit}><button className="close" type="button" onClick={onClose}><X /></button><p className="eyebrow">Capacity signal</p><h2>Update status kerja</h2><p className="muted">Sinyal ini menjadi konteks keputusan workload, bukan penilaian performa.</p><label>Kapasitas saat ini<select name="level" defaultValue={worker.latest_capacity_signal || 'BALANCED'}><option>AVAILABLE</option><option>BALANCED</option><option>NEAR_CAPACITY</option><option>OVER_CAPACITY</option></select></label>{error && <p className="form-error">{error}</p>}<button className="button" disabled={saving}>{saving ? 'Updating…' : 'Update status'}</button></form></div>; }

function ProgressForm({ assignments, onClose, onSaved }) { const [error, setError] = useState(''); const [saving, setSaving] = useState(false); const submit = async (event) => { event.preventDefault(); const form = new FormData(event.currentTarget); setSaving(true); try { const response = await fetch(`${API}/tasks/${form.get('task')}/`, { method: 'PATCH', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ progress: Number(form.get('progress')) }) }); if (!response.ok) throw new Error('Progress tidak dapat diperbarui.'); onSaved(); } catch (reason) { setError(reason.message); } setSaving(false); }; return <div className="modal-backdrop" role="dialog" aria-modal="true"><form className="modal" onSubmit={submit}><button className="close" type="button" onClick={onClose}><X /></button><p className="eyebrow">Work update</p><h2>Log waktu / progress</h2>{assignments.length ? <><label>Task<select name="task">{assignments.map(({ task }) => <option key={task.id} value={task.id}>{task.title}</option>)}</select></label><label>Progress (%)<input name="progress" min="0" max="100" type="number" required /></label></> : <p className="muted">Belum ada task yang bisa diperbarui.</p>}{error && <p className="form-error">{error}</p>}<button className="button" disabled={saving || !assignments.length}>{saving ? 'Saving…' : 'Save progress'}</button></form></div>; }
function Notifications({ blockers, tasks, analyses, onChoose }) { const reviews = tasks.filter((task) => analyses[task.id]?.recommendation?.review_candidates?.length); return <div className="page"><PageHeader eyebrow="Attention inbox" title="Notifications" detail="Perubahan kondisi selalu meminta review manusia." /><div className="notice-list">{blockers.map((blocker) => <button className="notice" key={blocker.id} onClick={() => onChoose(tasks.find((task) => task.id === blocker.task))}><CircleAlert /><span><strong>{titleize(blocker.type)} blocker</strong><p>{blocker.note}</p></span><ChevronRight /></button>)}{reviews.map((task) => <button className="notice" key={task.id} onClick={() => onChoose(task)}><Gauge /><span><strong>Review recommendation</strong><p>{task.title} memiliki kandidat yang perlu ditinjau.</p></span><ChevronRight /></button>)}{!blockers.length && !reviews.length && <Empty icon={CheckCircle2} title="Semua terkendali" detail="Tidak ada blocker atau workload review aktif." />}</div></div>; }
function SettingsPage() { return <div className="page"><PageHeader eyebrow="Workspace preferences" title="Settings" detail="Pantara menjaga keputusan assignment tetap transparan dan dapat ditinjau." /><div className="settings-card"><h2>Adaptive Engine</h2><p>Capability, capacity, dan access dievaluasi secara deterministik. Tidak ada auto-assignment atau leaderboard performa.</p><a className="button secondary" href="http://localhost:8000/api/docs/" target="_blank" rel="noreferrer">Open API documentation <ChevronRight size={16} /></a></div></div>; }

function TaskForm({ projects, onClose, onSaved }) { const [error, setError] = useState(''); const [saving, setSaving] = useState(false); const submit = async (event) => { event.preventDefault(); const form = new FormData(event.currentTarget); setSaving(true); setError(''); const payload = { project: form.get('project'), title: form.get('title'), description: form.get('description'), required_skills: form.get('skills').split(',').map((skill) => skill.trim()).filter(Boolean), complexity: form.get('complexity'), estimated_effort: Number(form.get('effort')), deadline: form.get('deadline') || null, access_requirements: form.get('access').split(',').map((item) => item.trim()).filter(Boolean) }; try { const response = await fetch(`${API}/tasks/`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) }); if (!response.ok) throw new Error((await response.json()).required_skills?.[0] || 'Task tidak dapat dibuat.'); onSaved(); } catch (reason) { setError(reason.message); } setSaving(false); }; return <div className="modal-backdrop" role="dialog" aria-modal="true" aria-label="Buat task"><form className="modal" onSubmit={submit}><button className="close" type="button" onClick={onClose} aria-label="Tutup"><X /></button><p className="eyebrow">New task</p><h2>Initialize work</h2><label>Project<select name="project" required defaultValue=""> <option value="" disabled>Pilih project</option>{projects.map((project) => <option key={project.id} value={project.id}>{project.name}</option>)}</select></label><label>Task title<input name="title" required placeholder="e.g. Implement workload review" /></label><label>Description<textarea name="description" rows="3" placeholder="Context for the team" /></label><div className="two-col"><label>Skills<input name="skills" required placeholder="React, TypeScript" /></label><label>Effort (hours)<input name="effort" min="1" type="number" required /></label></div><div className="two-col"><label>Complexity<select name="complexity" defaultValue="MEDIUM"><option>LOW</option><option>MEDIUM</option><option>HIGH</option></select></label><label>Deadline<input name="deadline" type="date" /></label></div><label>Access requirements<input name="access" placeholder="Remote, Screen Reader" /></label>{error && <p className="form-error">{error}</p>}<button className="button" disabled={saving}>{saving ? 'Saving…' : 'Create task'}</button></form></div>; }

export default App;
