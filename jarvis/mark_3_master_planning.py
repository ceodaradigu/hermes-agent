from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List


@dataclass(frozen=True)
class Mark3PlanningStatus:
    current_mark: str = "Mark 3 Planning"
    planning_only_in_this_pr: bool = True
    universal_governed_execution: bool = True
    mark_3_is_not_read_only: bool = True
    mark_3_is_not_preview_only: bool = True
    preview_first_default: bool = True
    execution_requires_valid_risk_approval: bool = True
    autonomous_mission_loop_planned: bool = True
    continuous_learning_planned: bool = True
    multi_agent_orchestration_planned: bool = True
    supervised_local_routines_planned: bool = True
    local_first_until_revenue_or_necessity: bool = True
    real_mark_3_execution_enabled_now: bool = False
    external_network_enabled_now: bool = False
    production_enabled_now: bool = False
    money_movement_enabled_now: bool = False
    access_material_enabled_now: bool = False
    safe_to_render: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class Mark3RiskApprovalLevel:
    level: int
    name: str
    approval_requirement: str
    scope: str
    examples: List[str] = field(default_factory=list)
    required_controls: List[str] = field(default_factory=list)
    intent_inference_allowed: bool = False
    executable_with_valid_approval: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class Mark3CapabilityArea:
    capability_id: str
    name: str
    objective: str
    planned_components: List[str] = field(default_factory=list)
    governance: List[str] = field(default_factory=list)
    success_signals: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class Mark3MacroRoadmapItem:
    pr_number: int
    title: str
    objective: str
    major_deliverables: List[str] = field(default_factory=list)
    exit_criteria: List[str] = field(default_factory=list)
    planning_only: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class Mark3Guardrail:
    guardrail_id: str
    rule: str
    rationale: str
    permanent_denial: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class Mark3ExecutionPrinciple:
    principle_id: str
    statement: str
    implications: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class Mark3PilotPlan:
    name: str = "Mark 3 governed local mission pilot"
    objective: str = "Validate the governed mission loop on useful local work before broader autonomy."
    environment: str = "David's current computer"
    stages: List[str] = field(default_factory=lambda: [
        "Select a bounded, reversible, useful mission.",
        "Classify risk, approval level, scope, budget, tools, and stop conditions.",
        "Generate plan and preview, then collect the required approval.",
        "Run only the approved candidate inside the approved scope.",
        "Capture evidence, real costs, outcomes, failures, and audit.",
        "Review post-mortem and propose approved learning and next action.",
    ])
    entry_criteria: List[str] = field(default_factory=lambda: [
        "Mission loop controls from PR #133 are tested.",
        "Risk classification and approval gates are inspectable.",
        "Kill switch, stop plan, audit, and bounded budget are available.",
        "No production, money movement, credentials, bulk email, or irreversible action is in scope.",
    ])
    success_metrics: List[str] = field(default_factory=lambda: [
        "No action exceeds approved scope, budget, tools, or risk level.",
        "Every side effect and approval is auditable.",
        "Outcomes and costs use evidence, with no fake costs or fake revenue.",
        "Human stop control remains visible and effective.",
        "Learning proposals require review before persistence or activation.",
    ])
    prohibited_in_initial_pilot: List[str] = field(default_factory=lambda: [
        "production deploy",
        "Stripe live or money movement",
        "DNS modification",
        "real bulk email",
        "credential storage or security bypass",
        "unbounded autonomy",
    ])
    safe_to_render: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def get_mark_3_planning_status() -> Dict[str, Any]:
    return Mark3PlanningStatus().to_dict()


def get_mark_3_execution_principles() -> Dict[str, Any]:
    principles = [
        Mark3ExecutionPrinciple(
            "not_cowardly_not_dishonest",
            "JARVIS must not be cowardly, and must not be dishonest.",
            [
                "Attempt ambitious legal, safe, authorized, technically possible work.",
                "Never claim success, capability, evidence, costs, or revenue without proof.",
            ],
        ),
        Mark3ExecutionPrinciple(
            "governed_execution",
            "Actions are blocked by default, executable with valid approval.",
            [
                "Preview and read-only are the default starting state, not the permanent ceiling.",
                "Risk determines approval strength, controls, scope, budget, audit, and rollback.",
            ],
        ),
        Mark3ExecutionPrinciple(
            "real_capability_boundary",
            "Permission cannot create a capability that tools and evidence do not support.",
            ["Unsupported work may become research or a prototype, but never a false execution claim."],
        ),
        Mark3ExecutionPrinciple(
            "human_control",
            "Human control remains visible and effective throughout governed execution.",
            ["Wake phrase is not permission.", "Critical actions require readback and stop or rollback plans."],
        ),
        Mark3ExecutionPrinciple(
            "local_first",
            "Operate local-first until revenue is sufficient or demonstrated technical necessity justifies cloud.",
            ["Do not recommend buying a Mac mini or VPS now.", "Measure costs and value before infrastructure spend."],
        ),
    ]
    return {"principles": [item.to_dict() for item in principles], "safe_to_render": True}


def get_mark_3_risk_approval_model() -> Dict[str, Any]:
    levels = [
        Mark3RiskApprovalLevel(
            0,
            "No extra permission",
            "No additional approval",
            "Innocuous reasoning and content work with no side effects.",
            ["summarize", "classify", "explain", "draft", "answer questions", "generate plans"],
            ["no side effects", "honest uncertainty"],
            intent_inference_allowed=True,
        ),
        Mark3RiskApprovalLevel(
            1,
            "Direct intent or contextual approval",
            "Direct instruction or contextual approval",
            "Low-risk, non-sensitive planning and analysis.",
            ["prepare report", "review docs", "detect improvements", "create checklist", "review supplied metrics"],
            ["context must be clear", "voice or tone may inform intent only for low-risk non-sensitive actions"],
            intent_inference_allowed=True,
        ),
        Mark3RiskApprovalLevel(
            2,
            "Simple approval",
            "Simple approval",
            "Small, bounded, reversible impact.",
            ["create worktree files", "modify documentation", "run tests", "controlled local repo inspection", "prepare PR candidates"],
            ["bounded scope", "audit", "no publication", "no sensitive material"],
        ),
        Mark3RiskApprovalLevel(
            3,
            "Explicit strong approval",
            "Explicit strong approval",
            "Sensitive actions, meaningful code changes, paid APIs, private data, or external side-effect candidates.",
            ["modify relevant code", "invoke real AI coding CLI", "use paid API", "access authorized private metrics", "modify routines"],
            ["exact scope", "strong approval", "budget", "audit", "stop plan", "authorized access only"],
        ),
        Mark3RiskApprovalLevel(
            4,
            "Double or triple confirmation",
            "Strong approval plus double confirmation; triple confirmation for very high risk",
            "Critical, irreversible, production, financial, identity, publication, deletion, or credential actions.",
            ["production deploy", "Stripe live", "move money", "modify DNS", "publish", "bulk email", "delete data", "touch credentials"],
            ["strong approval", "readback", "double confirmation", "triple confirmation when very high risk", "rollback or stop plan", "audit", "visible human control", "kill switch"],
        ),
        Mark3RiskApprovalLevel(
            5,
            "Permanent denial",
            "Denied regardless of approval claim",
            "Illegal, unsafe, harmful, unauthorized, deceptive, or security-bypass actions.",
            ["steal credentials", "steal cookies or tokens", "bypass 2FA", "unauthorized account access", "hide risk", "fake execution"],
            ["explain denial honestly", "offer legal and safe alternatives where possible"],
            executable_with_valid_approval=False,
        ),
    ]
    return {
        "levels": [item.to_dict() for item in levels],
        "wake_phrase_is_permission": False,
        "voice_tone_intent_rule": "Voice, tone, habits, context, and urgency may inform intent only for low-risk, non-sensitive actions.",
        "sensitive_actions_never_use_inferred_permission": True,
        "safe_to_render": True,
    }


def get_mark_3_capability_areas() -> Dict[str, Any]:
    definitions = [
        (
            "universal_governed_execution",
            "Universal Governed Execution",
            "Classify and govern any legal, safe, authorized, technically possible task.",
            ["task classification", "risk and permission", "scope and budget", "tool selection", "audit", "rollback and stop plan"],
            ["risk-scaled approvals", "real capability check", "human control"],
            ["no scope escape", "approval strength matches risk", "evidence-backed results"],
        ),
        (
            "autonomous_mission_loop",
            "Autonomous Mission Loop",
            "Move missions from intake through governed action, post-mortem, learning, and next action.",
            ["intake", "classification", "plan", "preview", "approval gates", "execution candidate", "result capture", "post-mortem"],
            ["bounded autonomy", "stop conditions", "approval gates"],
            ["mission outcomes captured", "no unapproved execution", "next action justified"],
        ),
        (
            "continuous_learning",
            "Continuous Learning System",
            "Learn from real outcomes without unsafe autoload or sensitive memory persistence.",
            ["approved memory", "tech radar", "experiment registry", "outcome memory", "failure memory", "ROI memory"],
            ["review before persistence", "no dangerous autoload", "no sensitive memory without approval"],
            ["learning linked to evidence", "reversible memory", "failures retained honestly"],
        ),
        (
            "multi_agent_orchestration",
            "Multi-Agent Orchestration",
            "Coordinate specialized agents under shared policy, budgets, locks, priority, and audit.",
            ["PlannerAgent", "BuilderAgent", "ReviewerAgent", "TesterAgent", "OperatorAgent", "ResearcherAgent", "ProductAgent", "CFOAgent", "SecurityAgent", "LegalRiskAgent", "GrowthAgent", "MemoryAgent", "RoutineAgent", "ToolRouterAgent"],
            ["per-agent permissions", "locks", "budgets", "conflict resolution", "handoff", "kill switch"],
            ["no conflicting side effects", "clear ownership", "auditable handoffs"],
        ),
        (
            "product_revenue_factory",
            "Product and Revenue Factory",
            "Turn validated opportunities into measurable product and monetization candidates.",
            ["opportunity detection", "niche validation", "SaaS blueprint", "landing candidate", "pricing", "Stripe candidate", "marketing plan", "measurement plan"],
            ["no fake revenue", "no fake costs", "publish and money gates"],
            ["evidence-based continue or kill decisions", "real conversion metrics", "bounded spend"],
        ),
        (
            "routine_scheduler",
            "Routine Scheduler and Supervised Autonomy",
            "Run useful recurring local work under supervision on David's current computer.",
            ["local routines", "periodic analysis", "reports", "repo health", "product health", "metrics health", "budget health"],
            ["local-first", "bounded schedules", "stop controls", "no 24/7 cloud before threshold"],
            ["reliable local runs", "useful reports", "no uncontrolled recurrence"],
        ),
        (
            "account_credential_assistance",
            "Account and Credential Assistance",
            "Help with owned or authorized accounts using official recovery and secure practices.",
            ["official recovery guidance", "secure account inventory", "password manager guidance", "2FA checklist", "family-authorized workflows", "access audit"],
            ["consent", "authorized scope", "never bypass security", "never expose or store plaintext secrets"],
            ["recovery through official flows", "stronger account security", "auditable consent"],
        ),
        (
            "moonshot_lab",
            "Moonshot Lab",
            "Research difficult or unsolved problems through hypotheses, experiments, prototypes, and evidence.",
            ["hypotheses", "advanced research", "experiment design", "prototype candidates", "evidence scoring", "uncertainty labels", "stage gates"],
            ["no overclaiming", "legal and safety review", "stage-gated risk"],
            ["reproducible evidence", "explicit uncertainty", "honest stop or continue decisions"],
        ),
        (
            "measurement_roi",
            "Measurement and ROI System",
            "Measure real costs, revenue, time, outcomes, confidence, and opportunity value.",
            ["real costs", "real revenue", "time invested", "tests", "conversions", "outcomes", "ROI", "opportunity score", "confidence score"],
            ["no_fake_costs", "no_fake_revenue", "source evidence"],
            ["traceable metrics", "honest unknowns", "better prioritization"],
        ),
        (
            "local_first_infrastructure",
            "Local-First Infrastructure Plan",
            "Keep JARVIS on David's current computer until revenue threshold or demonstrated technical necessity.",
            ["local runtime", "resource budgets", "revenue threshold", "necessity evidence", "future migration plan"],
            ["no Mac mini now", "no VPS now", "cloud only after threshold or demonstrated technical necessity"],
            ["cost stays bounded", "migration decision uses evidence", "local reliability measured"],
        ),
    ]
    areas = [Mark3CapabilityArea(*definition) for definition in definitions]
    return {"capabilities": [item.to_dict() for item in areas], "safe_to_render": True}


def get_mark_3_macro_roadmap() -> Dict[str, Any]:
    definitions = [
        (132, "Mark 3 Master Planning: Autonomous Learning Multi-Agent Roadmap", "Define architecture, policy, capabilities, risks, macro-phases, pilot, and success criteria.", ["pure planning module", "read-only planning endpoints", "tests", "master documentation"], ["planning model is deterministic", "Mark 3 is explicitly governed execution rather than permanent read-only"], True),
        (133, "Mark 3 Autonomous Mission Loop: Controlled Planner, Executor, Memory, Feedback", "Implement the first bounded governed mission loop.", ["mission intake", "risk classification", "approval gates", "result capture", "post-mortem"], ["bounded pilot candidate passes safety and lifecycle tests"], False),
        (134, "Mark 3 Governed Execution Engine", "Connect eligible bounded candidates to real governed execution without weakening approvals, audit, stop, or kill controls.", ["execution adapters", "runtime gates", "sandbox and rollback", "real evidence capture"], ["only exact eligible candidates can execute and every side effect is auditable"], False),
        (135, "Mark 3 Continuous Learning + Outcome Memory", "Persist evidence-linked outcomes and governed learning without turning memory into permission.", ["outcome and failure memory", "ROI memory", "experiments", "tech radar"], ["learning is reviewable, reversible, evidence-linked, and never permission"], False),
        (136, "Mark 3 Multi-Agent Orchestration", "Coordinate specialized agents without losing policy or human control.", ["agent roles", "permissions", "locks", "budgets", "handoffs", "conflict resolution"], ["agents cannot exceed role, budget, lock, or approval"], False),
        (137, "Mark 3 Product/Revenue Factory", "Build a governed opportunity, product, monetization, and measurement pipeline.", ["niche validation", "product blueprint", "landing and pricing candidates", "measurement", "kill or continue gate"], ["no fake revenue or costs; external actions remain risk-gated"], False),
        (138, "Mark 3 Local Routine Scheduler + Personal/Family Ops", "Run bounded recurring local work and authorized personal/family operations.", ["routine registry", "local scheduler", "health reports", "authorized account assistance", "official recovery", "consent", "password manager and 2FA guidance", "stop controls"], ["no uncontrolled recurrence, bypass, theft, or unauthorized access"], False),
        (139, "Mark 3 Moonshot Lab + Research/Experiment Engine", "Create an honest, stage-gated engine for ambitious research, experiments, and prototypes.", ["hypothesis registry", "experiments", "prototype candidates", "evidence scoring", "uncertainty"], ["no overclaiming; stage gates and safety review pass"], False),
        (140, "Mark 3 Release Candidate + Pilot", "Harden Mark 3 and run a real bounded pilot under visible human control.", ["cross-system audits", "kill switch verification", "pilot", "post-mortem", "RC runbook"], ["pilot evidence supports RC decision with no critical policy gaps"], False),
    ]
    items = [Mark3MacroRoadmapItem(*definition) for definition in definitions]
    return {
        "roadmap_strategy": "Large coherent macro-PRs; no micro-PR explosion.",
        "items": [item.to_dict() for item in items],
        "safe_to_render": True,
    }


def get_mark_3_guardrails() -> Dict[str, Any]:
    definitions = [
        ("approval_scales_with_risk", "Approval strength, scope, budget, audit, and rollback scale with risk.", "Governed execution replaces blanket prohibition.", False),
        ("wake_is_not_permission", "A wake phrase opens interaction and is never permission.", "Prevents accidental or ambient authorization.", False),
        ("intent_inference_low_risk_only", "Voice, tone, habits, context, and urgency may inform intent only for low-risk, non-sensitive work.", "Sensitive actions require explicit approval.", False),
        ("authorized_account_help", "Official recovery and security assistance is allowed for owned or explicitly authorized accounts.", "Security support is useful when consent and scope are real.", False),
        ("security_bypass_denied", "Unauthorized access, credential theft, cookie or token theft, and bypassing 2FA or controls are permanently denied.", "Authorization cannot legitimize theft or bypass.", True),
        ("no_deception", "Never hide risk, fake execution, invent capability, overclaim evidence, or promise unsupported success.", "JARVIS must not be dishonest.", True),
        ("moonshots_allowed", "Hard and unsolved problems may be researched, prototyped, and tested with explicit uncertainty.", "Ambition is allowed; unsupported claims are not.", False),
        ("legal_safe_authorized", "Illegal, unsafe, harmful, or unauthorized actions are permanently denied.", "These are hard boundaries rather than approval gates.", True),
        ("measurement_integrity", "Use real evidence for costs, revenue, outcomes, and confidence; preserve unknowns.", "No fake costs and no fake revenue.", False),
        ("memory_is_not_permission", "Learning and memory never grant action permission and sensitive memory needs approval.", "Prevents stale or sensitive memory from becoming authority.", False),
        ("local_first", "Stay on David's current computer until revenue threshold or demonstrated technical necessity.", "Infrastructure spend must follow evidence.", False),
    ]
    items = [Mark3Guardrail(*definition) for definition in definitions]
    return {"guardrails": [item.to_dict() for item in items], "safe_to_render": True}


def get_mark_3_pilot_plan() -> Dict[str, Any]:
    return Mark3PilotPlan().to_dict()


def get_mark_3_readiness() -> Dict[str, Any]:
    return {
        "current_mark": "Mark 3 Planning",
        "planning_pr_ready": True,
        "architecture_defined": True,
        "risk_approval_model_defined": True,
        "macro_roadmap_defined": True,
        "pilot_plan_defined": True,
        "mark_3_execution_ready_now": False,
        "free_autonomy_ready": False,
        "production_ready": False,
        "next_macro_pr": "PR #133 - Mark 3 Autonomous Mission Loop",
        "required_before_first_governed_execution": [
            "Implement and test the bounded mission loop.",
            "Connect risk classification to approval gates without bypass.",
            "Provide scope, budget, audit, stop, rollback, and kill-switch controls.",
            "Validate a local controlled pilot before broadening autonomy.",
        ],
        "success_metrics": [
            "Useful missions complete without exceeding approved risk, scope, budget, or tools.",
            "Every material action, approval, cost, result, and failure is auditable.",
            "Learning is evidence-linked, reviewable, reversible, and never permission.",
            "Multi-agent work respects roles, locks, budgets, conflicts, and human stop control.",
            "Revenue, costs, outcomes, and capability claims are never fabricated.",
        ],
        "safe_to_render": True,
    }
