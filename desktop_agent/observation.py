from typing import Optional
from .models import Observation, ObservationScope, DesktopAgentState, WindowRef, UIState


class DesktopToolsFacade:
    """
    Mock/placeholder for the actual desktop tools capability layer.
    In production, this would bridge to capabilities/desktop/.
    """

    @staticmethod
    def list_all_windows():
        return []

    @staticmethod
    def get_active_window_info():
        return WindowRef(title="Desktop")

    @staticmethod
    def get_ui_tree():
        return UIState(windows=[])

    @staticmethod
    def get_screenshot():
        return "/tmp/screen.png"


class ObservationManager:
    def __init__(self):
        self.current_observation: Optional[Observation] = None
        self.is_stale: bool = True

    def acquire(
        self, scope: ObservationScope = ObservationScope.UI_TREE
    ) -> Observation:
        if scope == ObservationScope.WINDOW_LIST:
            windows = DesktopToolsFacade.list_all_windows()
            active = DesktopToolsFacade.get_active_window_info()
            return Observation(scope=scope, active_window=active, windows=windows)

        elif scope == ObservationScope.UI_TREE:
            active = DesktopToolsFacade.get_active_window_info()
            tree = DesktopToolsFacade.get_ui_tree()
            return Observation(scope=scope, active_window=active, ui_tree=tree)

        elif scope == ObservationScope.SCREENSHOT:
            active = DesktopToolsFacade.get_active_window_info()
            path = DesktopToolsFacade.get_screenshot()
            tree = DesktopToolsFacade.get_ui_tree()
            return Observation(
                scope=scope, active_window=active, ui_tree=tree, screenshot_path=path
            )

        else:  # FULL or others
            active = DesktopToolsFacade.get_active_window_info()
            return Observation(scope=scope, active_window=active)

    def refresh_if_stale(
        self,
        state: DesktopAgentState,
        scope: ObservationScope = ObservationScope.UI_TREE,
    ):
        if self.is_stale:
            obs = self.acquire(scope)
            state.current_observation = obs
            self.current_observation = obs
            self.is_stale = False

    def mark_stale(self):
        self.is_stale = True

    def determine_required_scope(self, state: DesktopAgentState) -> ObservationScope:
        if not state.trajectory:
            return ObservationScope.UI_TREE

        current_milestone = None
        for m in state.trajectory.milestones:
            if m.milestone_id == state.current_milestone_id:
                current_milestone = m
                break

        if not current_milestone:
            return ObservationScope.UI_TREE

        desc = current_milestone.description.lower()
        if "window" in desc:
            return ObservationScope.WINDOW_LIST
        if "visual" in desc or "screenshot" in desc:
            return ObservationScope.SCREENSHOT

        return ObservationScope.UI_TREE
