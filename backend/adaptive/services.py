"""
Deterministic Adaptive Engine for Pantara-MindCraft.
Calculates 3 dimensions:
1. Capability Fit (0-2) -> Strong / Partial / Limited
2. Capacity Fit (0-2) -> Available / Balanced / Near Capacity / Over Capacity
3. Access Readiness (0-2) -> Ready / Needs Support / Unresolved

Candidate Score = Capability Fit + Capacity Fit + Access Readiness
"""
from typing import List, Dict, Any
from core.models import Member, WorkProfile, CapacitySignal, CapacityLevel
from work.models import Task, TaskStatus
from adaptive.models import CapabilityFit, CapacityFit, AccessReadiness


class AdaptiveEngine:

    @staticmethod
    def calculate_capability(task: Task, profile: WorkProfile) -> Dict[str, Any]:
        req_skills = [s.lower() for s in task.required_skills]
        if not req_skills:
            return {
                'fit': CapabilityFit.STRONG,
                'score': 2.0,
                'matched_skills': [],
                'missing_skills': [],
                'evidence': 'No specific required skills specified.'
            }

        member_skills = [s.lower() for s in profile.skills]
        matched = [s for s in req_skills if s in member_skills]
        missing = [s for s in req_skills if s not in member_skills]

        match_ratio = len(matched) / len(req_skills) if req_skills else 1.0

        # Check experience evidence
        exp_skills = [e.get('skill', '').lower() for e in profile.experience if isinstance(e, dict)]
        has_prior_exp = any(s in exp_skills for s in matched)

        if match_ratio == 1.0:
            fit = CapabilityFit.STRONG
            score = 2.0
            evidence = f"Memiliki seluruh keahlian yang dibutuhkan ({', '.join(matched)})."
        elif match_ratio >= 0.5:
            fit = CapabilityFit.PARTIAL
            score = 1.0
            evidence = f"Memiliki sebagian keahlian ({', '.join(matched)}), butuh adaptasi pada ({', '.join(missing)})."
        else:
            fit = CapabilityFit.LIMITED
            score = 0.0
            evidence = f"Keahlian belum sesuai ({', '.join(missing)})."

        if has_prior_exp:
            evidence += " Memiliki riwayat pengerjaan serupa sebelumnya."

        return {
            'fit': fit,
            'score': score,
            'matched_skills': matched,
            'missing_skills': missing,
            'evidence': evidence
        }

    @staticmethod
    def calculate_capacity(member: Member, task: Task) -> Dict[str, Any]:
        # Active assignments
        active_assignments = member.assignments.filter(
            task__status__in=[TaskStatus.PENDING, TaskStatus.IN_PROGRESS]
        )
        current_hours = sum(a.task.estimated_effort for a in active_assignments)
        projected_hours = current_hours + task.estimated_effort

        # Latest capacity signal
        latest_signal = member.capacity_signals.order_by('-created_at').first()
        signal_level = latest_signal.level if latest_signal else CapacityLevel.BALANCED

        # Scoring heuristics based on hours & signal
        # Baseline capacity: ~40h max standard workload
        if signal_level == CapacityLevel.OVER_CAPACITY or current_hours >= 35:
            fit = CapacityFit.OVER_CAPACITY
            score = 0.0
            evidence = f"Kapasitas penuh (Active: {current_hours}h, Signal: {signal_level}). Menambah beban berisiko overload."
        elif signal_level == CapacityLevel.NEAR_CAPACITY or current_hours >= 25:
            fit = CapacityFit.NEAR_CAPACITY
            score = 0.8
            evidence = f"Mendekati kapasitas maksimal (Active: {current_hours}h). Masih memungkinkan untuk task prioritas."
        elif signal_level == CapacityLevel.BALANCED or current_hours >= 15:
            fit = CapacityFit.BALANCED
            score = 1.5
            evidence = f"Beban kerja seimbang (Active: {current_hours}h). Kapasitas cukup untuk task baru."
        else:
            fit = CapacityFit.AVAILABLE
            score = 2.0
            evidence = f"Kapasitas sangat tersedia (Active: {current_hours}h, Signal: {signal_level})."

        return {
            'fit': fit,
            'score': score,
            'current_hours': current_hours,
            'projected_hours': projected_hours,
            'signal_level': signal_level,
            'active_tasks_count': active_assignments.count(),
            'evidence': evidence
        }

    @staticmethod
    def calculate_access(task: Task, profile: WorkProfile) -> Dict[str, Any]:
        req_access = [a.lower() for a in task.access_requirements]
        if not req_access:
            return {
                'readiness': AccessReadiness.READY,
                'score': 2.0,
                'matched_preferences': [],
                'unmet_preferences': [],
                'evidence': 'Tidak ada persyaratan akses khusus untuk task ini.'
            }

        member_prefs = [p.lower() for p in profile.access_preferences]
        matched = [a for a in req_access if a in member_prefs]
        unmet = [a for a in req_access if a not in member_prefs]

        if not unmet:
            readiness = AccessReadiness.READY
            score = 2.0
            evidence = f"Kebutuhan akses ({', '.join(req_access)}) terpenuhi oleh preferensi kerja."
        elif matched:
            readiness = AccessReadiness.NEEDS_SUPPORT
            score = 1.0
            evidence = f"Sebagian kebutuhan akses terpenuhi, memerlukan penyesuaian untuk: ({', '.join(unmet)})."
        else:
            readiness = AccessReadiness.UNRESOLVED
            score = 0.0
            evidence = f"Kebutuhan akses belum terkonfirmasi ({', '.join(unmet)}). Perlu klarifikasi sebelum assignment."

        return {
            'readiness': readiness,
            'score': score,
            'matched_preferences': matched,
            'unmet_preferences': unmet,
            'evidence': evidence
        }

    @classmethod
    def analyze_task(cls, task: Task) -> Dict[str, Any]:
        team = task.project.team
        members = team.members.all()

        candidates_data = []

        for member in members:
            # Ensure work profile exists
            profile, _ = WorkProfile.objects.get_or_create(member=member)

            capability = cls.calculate_capability(task, profile)
            capacity = cls.calculate_capacity(member, task)
            access = cls.calculate_access(task, profile)

            total_score = round(capability['score'] + capacity['score'] + access['score'], 2)

            candidates_data.append({
                'member_id': str(member.id),
                'member_name': member.name,
                'role': member.role,
                'total_score': total_score,
                'capability': capability,
                'capacity': capacity,
                'access': access,
                'is_eligible': access['readiness'] != AccessReadiness.UNRESOLVED
            })

        # Sort by total score descending
        candidates_data.sort(key=lambda x: (x['is_eligible'], x['total_score']), reverse=True)

        if not candidates_data:
            return {
                'candidates': [],
                'recommendation': {'reason': 'Tidak ada anggota tim yang terdaftar.'},
                'evidence': {},
                'workload_impact': {}
            }

        top_candidate = candidates_data[0]
        alternatives = candidates_data[1:3] if len(candidates_data) > 1 else []

        # Generate readable recommendation explanation
        reasons = []
        if top_candidate['capability']['fit'] == CapabilityFit.STRONG:
            reasons.append("memiliki keahlian yang sangat cocok")
        elif top_candidate['capability']['fit'] == CapabilityFit.PARTIAL:
            reasons.append("memiliki kemampuan yang cukup dengan potensi adaptasi")

        if top_candidate['capacity']['fit'] in [CapacityFit.AVAILABLE, CapacityFit.BALANCED]:
            reasons.append("memiliki kapasitas beban kerja yang sehat dan tersedia")
        else:
            reasons.append("sedang dalam beban kerja aktif")

        if top_candidate['access']['readiness'] == AccessReadiness.READY:
            reasons.append("kondisi akses kerja sudah selaras")

        recommendation_text = f"{top_candidate['member_name']} direkomendasikan karena " + ", ".join(reasons) + "."

        recommendation = {
            'recommended_member_id': top_candidate['member_id'],
            'recommended_member_name': top_candidate['member_name'],
            'score': top_candidate['total_score'],
            'reason': recommendation_text,
            'alternatives': [
                {
                    'member_id': alt['member_id'],
                    'member_name': alt['member_name'],
                    'score': alt['total_score'],
                    'summary': f"{alt['capability']['fit']} capability, {alt['capacity']['fit']} capacity"
                }
                for alt in alternatives
            ]
        }

        workload_impact = {
            c['member_name']: {
                'before_hours': c['capacity']['current_hours'],
                'after_hours': c['capacity']['projected_hours'],
                'signal': c['capacity']['signal_level']
            }
            for c in candidates_data
        }

        return {
            'candidates': candidates_data,
            'recommendation': recommendation,
            'evidence': {
                'task_title': task.title,
                'complexity': task.complexity,
                'estimated_effort': task.estimated_effort,
                'required_skills': task.required_skills,
                'access_requirements': task.access_requirements,
            },
            'workload_impact': workload_impact
        }
