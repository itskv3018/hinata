# core/planner.py
# Task planner — breaks complex requests into multi-step plans.

from utils.logger import get_logger

log = get_logger("planner")


class TaskPlanner:
    """
    Takes a complex user request and breaks it into an ordered
    sequence of plugin actions. Works with the LLM reasoner.
    """

    def __init__(self):
        self.active_plans: dict = {}  # plan_id → plan state

    def create_plan(self, steps: list, plan_id: str = None) -> dict:
        """Create a new execution plan."""
        import uuid
        plan_id = plan_id or str(uuid.uuid4())[:8]
        plan = {
            "id": plan_id,
            "steps": steps,
            "current_step": 0,
            "status": "pending",
            "results": [],
        }
        self.active_plans[plan_id] = plan
        log.info(f"📋 Plan {plan_id} created with {len(steps)} steps")
        return plan

    def get_next_step(self, plan_id: str) -> dict | None:
        """Get the next step in a plan."""
        plan = self.active_plans.get(plan_id)
        if not plan or plan["current_step"] >= len(plan["steps"]):
            return None
        return plan["steps"][plan["current_step"]]

    def complete_step(self, plan_id: str, result: str):
        """Mark the current step as complete and advance."""
        plan = self.active_plans.get(plan_id)
        if plan:
            plan["results"].append(result)
            plan["current_step"] += 1
            if plan["current_step"] >= len(plan["steps"]):
                plan["status"] = "completed"
                log.info(f"✅ Plan {plan_id} completed")

    def get_plan_status(self, plan_id: str) -> dict | None:
        """Get the status of a plan."""
        return self.active_plans.get(plan_id)
