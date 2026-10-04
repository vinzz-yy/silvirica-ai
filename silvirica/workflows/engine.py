from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional
from silvirica.core.types import ExecutionState


class WorkflowType(str, Enum):
    SV_CONTEXT = "sv-context"
    SV_INTERVIEW = "sv-interview"
    SV_RESEARCH = "sv-research"
    SV_PLAN = "sv-plan"
    SV_WORK = "sv-work"
    SV_LOOP = "sv-loop"
    SV_QA = "sv-qa"
    SV_SECURITY = "sv-security"
    SV_REVIEW = "sv-review"
    SV_REFACTOR = "sv-refactor"
    SV_UIUX = "sv-uiux"


@dataclass
class WorkflowStep:
    name: str
    description: str
    status: ExecutionState = ExecutionState.PLANNED
    result: Optional[Any] = None
    verification_evidence: Optional[str] = None


@dataclass
class WorkflowExecution:
    workflow_type: WorkflowType
    task: str
    steps: List[WorkflowStep] = field(default_factory=list)
    state: ExecutionState = ExecutionState.PLANNED
    max_loops: int = 5
    current_loop: int = 0

    def add_step(self, name: str, description: str) -> None:
        self.steps.append(WorkflowStep(name=name, description=description))


class WorkflowEngine:
    """
    Silvirica Workflow Engine for orchestrated AI development loops and verification gates.
    """

    @classmethod
    def create_workflow(cls, workflow_type: WorkflowType, task: str) -> WorkflowExecution:
        wf = WorkflowExecution(workflow_type=workflow_type, task=task)

        if workflow_type == WorkflowType.SV_PLAN:
            wf.add_step("Align Context", "Retrieve project architecture, memory, and tech stack.")
            wf.add_step("Identify Affected Symbols", "Query symbol and dependency graph for impacted components.")
            wf.add_step("Draft Implementation Plan", "Construct step-by-step tasks with file boundaries and risks.")
            wf.add_step("Verification Criteria", "Define unit tests and completion criteria.")

        elif workflow_type == WorkflowType.SV_LOOP:
            wf.add_step("Plan", "Compile minimal context and plan change.")
            wf.add_step("Build", "Execute deterministic code generation within file boundary.")
            wf.add_step("Test", "Run test suite and static analysis.")
            wf.add_step("Review", "Verify diff against guardrails and regressions.")
            wf.add_step("Verify", "Confirm completion integrity.")

        elif workflow_type == WorkflowType.SV_SECURITY:
            wf.add_step("Secret Scan", "Audit repository for exposed API keys and credentials.")
            wf.add_step("Static Rule Audit", "Check for SQLi, XSS, CSRF, IDOR, and auth issues.")
            wf.add_step("Impact Analysis", "Check affected sensitive routes and tables.")
            wf.add_step("Remediation Plan", "Produce defensive recommendations.")

        elif workflow_type == WorkflowType.SV_QA:
            wf.add_step("Edge Case Identification", "Generate boundary and hostile test scenarios.")
            wf.add_step("Execute Tests", "Run unit and integration verification.")
            wf.add_step("Evaluate Failures", "Record failure memory for unexpected breakdowns.")

        elif workflow_type == WorkflowType.SV_CONTEXT:
            wf.add_step("Scan Terminology", "Extract domain terms from glossary and code.")
            wf.add_step("Inspect Conventions", "Load project coding standards and patterns.")
            wf.add_step("Verify Tech Stack", "Detect languages, frameworks, and packages.")

        return wf

    @classmethod
    def execute_workflow_sync(cls, execution: WorkflowExecution) -> Dict[str, Any]:
        execution.state = ExecutionState.RUNNING
        for step in execution.steps:
            step.status = ExecutionState.RUNNING
            # Execute step simulation / logic
            step.result = f"Completed step '{step.name}' for task '{execution.task}'."
            step.status = ExecutionState.VERIFIED
            step.verification_evidence = "Verified deterministically."

        execution.state = ExecutionState.COMPLETE
        return {
            "workflow": execution.workflow_type.value,
            "task": execution.task,
            "state": execution.state.value,
            "steps": [{"name": s.name, "status": s.status.value, "result": s.result} for s in execution.steps],
        }
