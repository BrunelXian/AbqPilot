from __future__ import annotations

import json
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, ttk

from abqpilot.gui.action_controller import GuiActionController
from abqpilot.gui.style import (
    APP_TITLE,
    CTK,
    DISABLED_ACTION_MESSAGE,
    HAS_CUSTOMTKINTER,
    configure_ttk_style,
    configure_window_theme,
)
from abqpilot.gui.widgets import artifact_preview, make_button, make_frame, make_label, make_listbox, make_text, set_text


PROJECT_ROOT = Path(__file__).resolve().parents[2]
BaseWindow = CTK.CTk if HAS_CUSTOMTKINTER else tk.Tk


class AbqPilotGui(BaseWindow):
    def __init__(self, task_dir: str | None = None, project_root: str | Path = PROJECT_ROOT) -> None:
        super().__init__()
        self.title(APP_TITLE)
        self.geometry("1400x860")
        configure_window_theme(self)
        configure_ttk_style(self)
        self.project_root = Path(project_root)
        self.controller = GuiActionController(self.project_root)
        self.task_dir = Path(task_dir) if task_dir else None
        self.view_model: dict | None = None
        self.recent_tasks: list[dict] = []
        self._build_layout()
        self._load_recent_tasks()
        if self.task_dir:
            self.refresh()

    def _build_layout(self) -> None:
        self.columnconfigure(1, weight=1)
        self.rowconfigure(1, weight=1)

        top = make_frame(self, padding=10, panel=True)
        top.grid(row=0, column=0, columnspan=3, sticky="ew")
        top.columnconfigure(3, weight=1)
        make_label(top, text=APP_TITLE, font=("Segoe UI", 18, "bold")).grid(row=0, column=0, padx=(14, 18), pady=10)
        self.task_label = make_label(top, text="Task: not loaded", muted=True)
        self.task_label.grid(row=0, column=1, padx=(0, 14))
        self.status_label = make_label(top, text="Overall: idle", muted=True)
        self.status_label.grid(row=0, column=2, padx=(0, 14))
        make_button(top, "Refresh", self.refresh).grid(row=0, column=4, padx=4)
        make_button(top, "Report", self._export_report).grid(row=0, column=5, padx=4)

        self.left = make_frame(self, padding=10, panel=True)
        self.left.grid(row=1, column=0, sticky="nsw", padx=(10, 5), pady=10)
        self.center = make_frame(self, padding=10, panel=True)
        self.center.grid(row=1, column=1, sticky="nsew", padx=5, pady=10)
        self.right = make_frame(self, padding=10, panel=True)
        self.right.grid(row=1, column=2, sticky="nse", padx=(5, 10), pady=10)
        self.center.rowconfigure(1, weight=1)
        self.center.columnconfigure(0, weight=1)

        self._build_left_sidebar()
        self._build_center_panel()
        self._build_right_panel()

        bottom = make_frame(self, padding=8, panel=True)
        bottom.grid(row=2, column=0, columnspan=3, sticky="ew")
        self.bottom_label = make_label(bottom, text="Ready", muted=True)
        self.bottom_label.pack(anchor="w", padx=12, pady=6)

    def _build_left_sidebar(self) -> None:
        make_button(self.left, "Load Task", self.load_task).pack(fill="x", pady=(0, 4))
        make_button(self.left, "Refresh Recent", self._load_recent_tasks).pack(fill="x", pady=(0, 8))

        make_label(self.left, text="Recent Tasks", font=("Segoe UI", 11, "bold")).pack(anchor="w", padx=8, pady=(8, 2))
        self.recent_list = make_listbox(self.left, width=36, height=7)
        self.recent_list.pack(fill="x", pady=(0, 8))
        self.recent_list.bind("<Double-Button-1>", self._recent_selected)

        make_label(self.left, text="Pipeline Steps", font=("Segoe UI", 11, "bold")).pack(anchor="w", padx=8, pady=(8, 2))
        self.module_list = make_listbox(self.left, width=36, height=11)
        self.module_list.pack(fill="x", pady=(0, 8))

        make_label(self.left, text="Artifacts", font=("Segoe UI", 11, "bold")).pack(anchor="w", padx=8, pady=(8, 2))
        self.artifact_list = make_listbox(self.left, width=36, height=10)
        self.artifact_list.pack(fill="x", pady=(0, 8))
        self.artifact_list.bind("<<ListboxSelect>>", self._artifact_selected)

        make_label(self.left, text="Workflow Presets", font=("Segoe UI", 11, "bold")).pack(anchor="w", padx=8, pady=(8, 2))
        self.preset_list = make_listbox(self.left, width=36, height=6)
        self.preset_list.pack(fill="x")
        for preset in self.controller.presets().get("presets", []):
            self.preset_list.insert("end", preset["display_name"])
        self.preset_list.bind("<<ListboxSelect>>", self._preset_selected)

    def _build_center_panel(self) -> None:
        make_label(self.center, text="Event Stream", font=("Segoe UI", 12, "bold")).grid(row=0, column=0, sticky="w", padx=10, pady=(10, 4))
        self.event_text = make_text(self.center, height=28)
        self.event_text.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        make_label(self.center, text="Artifact Preview", font=("Segoe UI", 12, "bold")).grid(row=2, column=0, sticky="w", padx=10, pady=(4, 4))
        self.preview_text = make_text(self.center, height=8)
        self.preview_text.grid(row=3, column=0, sticky="ew", padx=10, pady=(0, 10))
        make_label(self.center, text="Reasoning Panel", font=("Segoe UI", 12, "bold")).grid(row=4, column=0, sticky="w", padx=10, pady=(4, 4))
        self.reasoning_text = make_text(self.center, height=7)
        self.reasoning_text.grid(row=5, column=0, sticky="ew", padx=10, pady=(0, 10))
        make_label(self.center, text="Patch Proposal Panel", font=("Segoe UI", 12, "bold")).grid(row=6, column=0, sticky="w", padx=10, pady=(4, 4))
        self.patch_text = make_text(self.center, height=7)
        self.patch_text.grid(row=7, column=0, sticky="ew", padx=10, pady=(0, 10))

    def _build_right_panel(self) -> None:
        make_label(self.right, text="Current Worker", font=("Segoe UI", 12, "bold")).pack(anchor="w", padx=10, pady=(10, 4))
        self.right_text = make_text(self.right, width=46, height=27)
        self.right_text.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        buttons = make_frame(self.right, panel=False)
        buttons.pack(fill="x", padx=10, pady=(8, 10))
        for label, command in [
            ("Run Prepare Pipeline", self._run_prepare_pipeline),
            ("Create Approval Token", self._create_approval_token),
            ("Poll JobPilot Status", self._poll_status),
            ("Continue From Job Output", self._continue_output),
            ("Generate Repair Plan", self._repair_plan),
            ("Export Run Report", self._export_report),
            ("Open Artifact Folder", self._show_artifact_folder),
            ("Run Mock Reasoner", self._run_mock_reasoner),
            ("Preview LLM Input Summary", self._preview_llm_summary),
            ("Run Real LLM Reasoner", self._run_real_llm_reasoner),
            ("Propose Patch with Mock LLM", self._propose_patch_mock),
            ("Preview Patch Context", self._preview_patch_context),
            ("Propose Patch with Real LLM", self._propose_patch_real),
            ("Preview Guarded Patch", self._preview_guarded_patch),
            ("Preview DFLUX Deactivation Patch", self._preview_dflux_deactivation_patch),
            ("Run Model Condition Preservation Guard", self._run_model_condition_guard),
            ("Prepare DFLUX-Guarded Solver Run", self._prepare_dflux_guarded_solver_run),
            ("Approve DFLUX-Guarded Solver Run", self._approve_dflux_guarded_solver_run),
            ("Run Approved DFLUX-Guarded Solver", self._run_dflux_guarded_solver),
            ("Monitor DFLUX-Guarded Solver", self._monitor_dflux_guarded_solver),
            ("Intake DFLUX-Guarded Solver Output", self._intake_dflux_guarded_solver_output),
            ("Report DFLUX-Guarded Solver Run", self._report_dflux_guarded_solver_run),
            ("Queue Patch Preview: Preflight", self._queue_patch_preflight),
            ("Queue Patch Preview: Dry-Run Enqueue", self._queue_patch_dry_run),
            ("Create Patch Queue Approval Token", self._create_patch_queue_approval),
            ("Queue Patch Preview: Real Queue-Only Enqueue", self._queue_patch_real),
            ("Poll Patch Queue Status", self._poll_patch_queue),
            ("Poll Patched Job Status", self._poll_patch_queue),
            ("Intake Patched Job Output", self._intake_patched_job_output),
            ("Extract Patched Job Metrics", self._extract_patched_job_metrics),
            ("Report Patched Job", self._report_patched_job),
            ("Prepare Controlled Solver Run", self._prepare_controlled_solver_run),
            ("Approve Controlled Solver Run", self._approve_controlled_solver_run),
            ("Run Approved Solver", self._run_approved_solver),
            ("Monitor Solver Run", self._monitor_controlled_solver_run),
            ("Diagnose Job / ODB Output", self._diagnose_job_output),
            ("List abqjobpilot Job Records", self._list_abqjobpilot_records),
            ("Diagnose from abqjobpilot Record", self._diagnose_from_abqjobpilot_record),
            ("Propose Solver Failure Repair", self._propose_solver_failure_repair),
            ("Intake Solver Output", self._intake_solver_output),
            ("Report Solver Run", self._report_solver_run),
        ]:
            make_button(buttons, label, command).pack(fill="x", pady=3)

        ttk.Separator(buttons).pack(fill="x", pady=6)
        for label in [
            "Start Abaqus Solver [DISABLED]",
            "Launch " + "Queue" + "Runner [DISABLED]",
            "Run LLM Agent [DISABLED]",
            "Auto Repair INP [DISABLED]",
            "Apply Patch [DISABLED]",
            "Run Patched Solver [DISABLED]",
            "Batch Auto Loop [DISABLED]",
            "LLM Run Solver [DISABLED]",
            "Arbitrary Command [DISABLED]",
            "Auto Retry Loop [DISABLED]",
        ]:
            make_button(buttons, label, lambda name=label: self._blocked_action(name), danger=True).pack(fill="x", pady=3)

    def load_task(self) -> None:
        selected = filedialog.askdirectory(title="Select AbqPilot task directory")
        if selected:
            self.task_dir = Path(selected)
            self.refresh()

    def refresh(self) -> None:
        if not self.task_dir:
            self._set_status("No task loaded")
            return
        result = self.controller.refresh_task(self.task_dir)
        if not result.get("success"):
            self._append_action_result(result)
            self._set_status("Refresh failed")
            return
        self.view_model = result["view_model"]
        self.task_label.configure(text=f"Task: {self.view_model.get('task_id')}")
        self.status_label.configure(text=f"Overall: {self.view_model.get('overall_status')}")
        self._render_modules()
        self._render_events()
        self._render_artifacts()
        self._render_right_panel()
        self._render_reasoning_panel()
        self._render_patch_panel()
        self._append_action_result(result)
        self._set_status("Ready")

    def _render_modules(self) -> None:
        self.module_list.delete(0, "end")
        for module in self.view_model.get("modules", []):
            self.module_list.insert("end", f"{module['display_name']}  [{module['status']}]")

    def _render_events(self) -> None:
        lines = []
        for event in self.view_model.get("events", [])[-240:]:
            timestamp = event.get("timestamp") or "--:--:--"
            title = event.get("title") or event.get("module_id")
            lines.append(f"[{timestamp}] {title}: {event.get('status') or event.get('message')}")
        set_text(self.event_text, "\n".join(lines))

    def _render_artifacts(self) -> None:
        self.artifact_list.delete(0, "end")
        for artifact in self.view_model.get("artifacts", []):
            self.artifact_list.insert("end", artifact.get("name"))

    def _render_right_panel(self) -> None:
        panel = self.view_model.get("right_panel", {})
        active = panel.get("active_artifacts", [])
        artifact_lines = [f"- {item.get('name')}: {item.get('path')}" for item in active[-8:]]
        text = "\n".join(
            [
                "Current Module",
                str(panel.get("module_name")),
                "",
                "Status",
                str(panel.get("status")),
                "",
                "Stage",
                str(panel.get("stage")),
                "",
                "Input Summary",
                str(panel.get("input_summary")),
                "",
                "Output Summary",
                str(panel.get("output_summary")),
                "",
                "Last Artifact",
                str(panel.get("last_artifact")),
                "",
                "Guard State",
                str(panel.get("guard_state")),
                "",
                "Next Allowed Action",
                str(panel.get("next_allowed_action")),
                "",
                "Active Artifacts",
                "\n".join(artifact_lines) if artifact_lines else "None",
            ]
        )
        set_text(self.right_text, text)

    def _render_reasoning_panel(self) -> None:
        if not self.task_dir:
            set_text(self.reasoning_text, "No task loaded.")
            return
        path = self.task_dir / "llm_reasoning" / "llm_reasoning_result.json"
        if not path.exists():
            set_text(self.reasoning_text, "No LLM reasoning artifact yet. Use mock reasoner or preview input summary.")
            return
        preview = artifact_preview(str(path))
        set_text(self.reasoning_text, preview)

    def _render_patch_panel(self) -> None:
        if not self.task_dir:
            set_text(self.patch_text, "No task loaded.")
            return
        path = self.task_dir / "llm_patch_proposals" / "llm_candidate_patch_proposal.json"
        preview_path = _latest_patch_preview_summary(self.task_dir)
        if preview_path is not None:
            set_text(self.patch_text, artifact_preview(str(preview_path)))
            return
        if not path.exists():
            set_text(self.patch_text, "No candidate patch proposal artifact yet. Use mock proposal or preview patch context.")
            return
        preview = artifact_preview(str(path))
        set_text(self.patch_text, preview)

    def _artifact_selected(self, _event=None) -> None:
        if not self.view_model:
            return
        selection = self.artifact_list.curselection()
        if not selection:
            return
        artifact = self.view_model.get("artifacts", [])[selection[0]]
        set_text(self.preview_text, artifact_preview(artifact.get("path")))

    def _recent_selected(self, _event=None) -> None:
        selection = self.recent_list.curselection()
        if not selection:
            return
        self.task_dir = Path(self.recent_tasks[selection[0]]["task_dir"])
        self.refresh()

    def _preset_selected(self, _event=None) -> None:
        selection = self.preset_list.curselection()
        if not selection:
            return
        preset = self.controller.presets().get("presets", [])[selection[0]]
        self._set_status(f"Preset selected: {preset['display_name']} - {preset['description']}")

    def _run_prepare_pipeline(self) -> None:
        config = filedialog.askopenfilename(title="Select task config JSON", filetypes=[("JSON", "*.json"), ("All files", "*.*")])
        if not config:
            return
        task_id = simpledialog.askstring("Task ID", "Task ID for prepare pipeline:")
        result = self.controller.run_prepare_pipeline(config, task_id=task_id, abqjobpilot_root=None)
        self._handle_action_result(result, "Prepare pipeline finished")

    def _create_approval_token(self) -> None:
        if not self.task_dir:
            self._set_status("Load a task first")
            return
        approved_by = simpledialog.askstring("Approved By", "Approved by:", initialvalue="human")
        phrase = simpledialog.askstring("Approval Phrase", "Exact approval phrase:", show=None)
        if not approved_by or not phrase:
            self._set_status("Approval token creation cancelled")
            return
        result = self.controller.create_approval_token(self.task_dir, approved_by=approved_by, approval_phrase=phrase)
        self._handle_action_result(result, "Approval token action finished")

    def _poll_status(self) -> None:
        self._require_task(lambda: self.controller.poll_jobpilot_status(self.task_dir), "Status poll complete")

    def _continue_output(self) -> None:
        self._require_task(lambda: self.controller.continue_from_job_output(self.task_dir), "Continuation check complete")

    def _repair_plan(self) -> None:
        self._require_task(lambda: self.controller.generate_repair_plan(self.task_dir), "Repair plan generated")

    def _export_report(self) -> None:
        self._require_task(lambda: self.controller.export_run_report(self.task_dir), "Run report exported")

    def _show_artifact_folder(self) -> None:
        if not self.task_dir:
            self._set_status("Load a task first")
            return
        result = self.controller.open_artifact_folder(self.task_dir)
        messagebox.showinfo("Artifact Folder", result.get("path"))
        self._append_action_result(result)

    def _run_mock_reasoner(self) -> None:
        self._require_task(lambda: self.controller.run_mock_reasoner(self.task_dir), "Mock reasoner complete")

    def _preview_llm_summary(self) -> None:
        if not self.task_dir:
            self._set_status("Load a task first")
            return
        result = self.controller.preview_llm_input_summary(self.task_dir)
        summary = result.get("details", {}).get("sanitized_summary")
        if summary is not None:
            import json

            set_text(self.reasoning_text, json.dumps(summary, indent=2, ensure_ascii=False, sort_keys=True))
        self._append_action_result(result)
        self._set_status("LLM input summary preview ready" if result.get("success") else result.get("verdict", "Preview failed"))

    def _run_real_llm_reasoner(self) -> None:
        if not self.task_dir:
            self._set_status("Load a task first")
            return
        confirmed = messagebox.askyesno(
            "Confirm Real LLM Reasoning",
            "Send a compact sanitized task summary to the configured provider?\n\n"
            "AbqPilot will not send full INP, ODB, CAE, logs, or secrets.",
        )
        result = self.controller.run_real_llm_reasoner(self.task_dir, confirmed=confirmed)
        self._handle_action_result(result, "Real LLM reasoning complete")

    def _propose_patch_mock(self) -> None:
        self._require_task(lambda: self.controller.propose_patch_mock(self.task_dir), "Mock patch proposal complete")

    def _preview_patch_context(self) -> None:
        if not self.task_dir:
            self._set_status("Load a task first")
            return
        result = self.controller.preview_patch_context(self.task_dir)
        context = result.get("details", {}).get("patch_context")
        if context is not None:
            import json

            set_text(self.patch_text, json.dumps(context, indent=2, ensure_ascii=False, sort_keys=True))
        self._append_action_result(result)
        self._set_status("Patch context preview ready" if result.get("success") else result.get("verdict", "Preview failed"))

    def _propose_patch_real(self) -> None:
        if not self.task_dir:
            self._set_status("Load a task first")
            return
        confirmed = messagebox.askyesno(
            "Confirm Real LLM Patch Proposal",
            "Send a compact sanitized patch context to the configured provider?\n\n"
            "AbqPilot will not send full INP, ODB, CAE, logs, or secrets. The LLM cannot apply patches.",
        )
        result = self.controller.propose_patch_real(self.task_dir, confirmed=confirmed)
        self._handle_action_result(result, "Real patch proposal complete")

    def _preview_guarded_patch(self) -> None:
        self._require_task(lambda: self.controller.preview_guarded_patch(self.task_dir), "Guarded patch preview complete")

    def _preview_dflux_deactivation_patch(self) -> None:
        source = Path("D:/Projects/AbqPilot-v2/runs/stage4_0_controlled_solver_automation/run_20260703_105833_589810/candidate_sanity_base_power_x2_stage4.inp")
        output = Path("D:/Projects/AbqPilot-v2/runs/stage4_3_guarded_dflux_deactivation_patch_preview")
        comparison = Path("D:/Projects/AbqPilot-v2/CAE_model/sanity_base")
        result = self.controller.preview_dflux_deactivation_patch(source, output, comparison)
        self._handle_action_result(result, "DFLUX deactivation patch preview complete")

    def _queue_patch_preflight(self) -> None:
        self._require_task(
            lambda: self.controller.queue_patch_preview_preflight(self.task_dir, _latest_patch_preview_dir(self.task_dir)),
            "Patch preflight complete",
        )

    def _queue_patch_dry_run(self) -> None:
        self._require_task(
            lambda: self.controller.queue_patch_preview_dry_run(self.task_dir, _latest_patch_preview_dir(self.task_dir)),
            "Patch dry-run enqueue complete",
        )

    def _create_patch_queue_approval(self) -> None:
        if not self.task_dir:
            self._set_status("Load a task first")
            return
        workflow = _latest_patch_queue_workflow(self.task_dir)
        if workflow is None:
            self._set_status("No patch queue workflow found")
            return
        phrase = simpledialog.askstring("Patch Queue Approval", "Enter the patch queue approval phrase:", show=None)
        if not phrase:
            self._set_status("Patch queue approval cancelled")
            return
        result = self.controller.create_patch_queue_approval_token(workflow, "human", phrase)
        self._handle_action_result(result, "Patch queue approval token created")

    def _queue_patch_real(self) -> None:
        if not self.task_dir:
            self._set_status("Load a task first")
            return
        workflow = _latest_patch_queue_workflow(self.task_dir)
        if workflow is None:
            self._set_status("No patch queue workflow found")
            return
        token = workflow / "approvals" / "patch_queue_approval_token.json"
        confirmed = messagebox.askyesno(
            "Confirm Patch Queue-Only Enqueue",
            "Queue this validated patch candidate only if its candidate-specific approval token is valid?\n\n"
            "No solver will be submitted. No external queue worker will be launched.",
        )
        if not confirmed:
            self._set_status("Patch queue-only enqueue cancelled")
            return
        result = self.controller.queue_patch_preview_real_queue_only(workflow, token)
        self._handle_action_result(result, "Patch queue-only enqueue complete")

    def _poll_patch_queue(self) -> None:
        if not self.task_dir:
            self._set_status("Load a task first")
            return
        workflow = _latest_patch_queue_workflow(self.task_dir)
        if workflow is None:
            self._set_status("No patch queue workflow found")
            return
        result = self.controller.poll_patch_queue_status(workflow)
        self._handle_action_result(result, "Patch queue status poll complete")

    def _intake_patched_job_output(self) -> None:
        if not self.task_dir:
            self._set_status("Load a task first")
            return
        workflow = _latest_patch_queue_workflow(self.task_dir)
        if workflow is None:
            self._set_status("No patch queue workflow found")
            return
        result = self.controller.intake_patched_job_output(workflow)
        self._handle_action_result(result, "Patched job output intake complete")

    def _extract_patched_job_metrics(self) -> None:
        if not self.task_dir:
            self._set_status("Load a task first")
            return
        workflow = _latest_patch_queue_workflow(self.task_dir)
        if workflow is None:
            self._set_status("No patch queue workflow found")
            return
        result = self.controller.extract_patched_job_metrics(workflow)
        self._handle_action_result(result, "Patched job metrics gate complete")

    def _report_patched_job(self) -> None:
        if not self.task_dir:
            self._set_status("Load a task first")
            return
        workflow = _latest_patch_queue_workflow(self.task_dir)
        if workflow is None:
            self._set_status("No patch queue workflow found")
            return
        result = self.controller.report_patched_job(workflow)
        self._handle_action_result(result, "Patched job report complete")

    def _prepare_controlled_solver_run(self) -> None:
        candidate = Path("D:/Projects/AbqPilot-v2/runs/stage3_9b_real_sanity_base_patch_candidate/candidate_sanity_base_power_x2.inp")
        source = Path("D:/Projects/AbqPilot-v2/runs/stage3_9b_real_sanity_base_patch_candidate/source_sanity_base_export.inp")
        evidence = Path("D:/Projects/AbqPilot-v2/runs/stage3_9b_real_sanity_base_patch_candidate")
        result = self.controller.prepare_controlled_solver_run(candidate, source, evidence, cpus=14)
        self._handle_action_result(result, "Controlled solver run prepared")

    def _approve_controlled_solver_run(self) -> None:
        solver_run = _latest_solver_run_dir()
        if solver_run is None:
            self._set_status("No controlled solver run found")
            return
        phrase = simpledialog.askstring("Controlled Solver Approval", "Enter the controlled solver approval phrase:", show=None)
        if not phrase:
            self._set_status("Controlled solver approval cancelled")
            return
        result = self.controller.approve_controlled_solver_run(solver_run, "human", phrase)
        self._handle_action_result(result, "Controlled solver approval token created")

    def _run_approved_solver(self) -> None:
        solver_run = _latest_solver_run_dir()
        if solver_run is None:
            self._set_status("No controlled solver run found")
            return
        confirmed = messagebox.askyesno(
            "Confirm Controlled Solver Run",
            "Run the approved single Abaqus solver job?\n\n"
            "Only the fixed command preview will be used. No external queue worker, no LLM, no arbitrary command.",
        )
        if not confirmed:
            self._set_status("Controlled solver run cancelled")
            return
        token = solver_run / "approvals" / "solver_run_approval_token.json"
        result = self.controller.run_approved_solver(solver_run, token)
        self._handle_action_result(result, "Controlled solver run finished")

    def _monitor_controlled_solver_run(self) -> None:
        solver_run = _latest_solver_run_dir()
        if solver_run is None:
            self._set_status("No controlled solver run found")
            return
        result = self.controller.monitor_solver_run(solver_run)
        self._handle_action_result(result, "Controlled solver monitor complete")

    def _diagnose_job_output(self) -> None:
        solver_run = _latest_solver_run_dir()
        if solver_run is None:
            self._set_status("No controlled solver run found")
            return
        result = self.controller.diagnose_job_output(solver_run, _latest_solver_job_name(solver_run))
        self._handle_action_result(result, "Job / ODB diagnosis complete")

    def _list_abqjobpilot_records(self) -> None:
        runtime = Path("D:/Projects/abqjobpilot_dev/runtime")
        result = self.controller.list_abqjobpilot_job_records(runtime)
        self._handle_action_result(result, "abqjobpilot records listed")

    def _diagnose_from_abqjobpilot_record(self) -> None:
        runtime = Path("D:/Projects/abqjobpilot_dev/runtime")
        result = self.controller.list_abqjobpilot_job_records(runtime)
        records = result.get("details", {}).get("records", []) if isinstance(result.get("details"), dict) else []
        if not records:
            self._set_status("No abqjobpilot records found")
            return
        job_id = records[0].get("job_id")
        result = self.controller.diagnose_from_abqjobpilot_record(job_id=job_id, runtime_dir=runtime)
        self._handle_action_result(result, "abqjobpilot-backed diagnosis complete")

    def _propose_solver_failure_repair(self) -> None:
        solver_run = _latest_solver_run_dir()
        if solver_run is None:
            self._set_status("No controlled solver run found")
            return
        result = self.controller.propose_solver_failure_repair(solver_run)
        self._handle_action_result(result, "Solver failure repair proposal ready")

    def _intake_solver_output(self) -> None:
        solver_run = _latest_solver_run_dir()
        if solver_run is None:
            self._set_status("No controlled solver run found")
            return
        result = self.controller.intake_solver_output(solver_run)
        self._handle_action_result(result, "Controlled solver output intake complete")

    def _report_solver_run(self) -> None:
        solver_run = _latest_solver_run_dir()
        if solver_run is None:
            self._set_status("No controlled solver run found")
            return
        result = self.controller.report_solver_run(solver_run)
        self._handle_action_result(result, "Controlled solver report complete")

    def _prepare_dflux_guarded_solver_run(self) -> None:
        preview = Path("D:/Projects/AbqPilot-v2/runs/stage4_3_guarded_dflux_deactivation_patch_preview/candidate_sanity_base_power_x2_stage4_dflux_deactivated_preview.inp")
        validation = Path("D:/Projects/AbqPilot-v2/runs/stage4_3_guarded_dflux_deactivation_patch_preview/dflux_lifecycle_validation.json")
        output = Path("D:/Projects/AbqPilot-v2/runs/stage4_4_dflux_deactivated_controlled_solver_validation")
        result = self.controller.prepare_dflux_guarded_solver_run(preview, validation, output)
        self._handle_action_result(result, "DFLUX-guarded solver run prepared")

    def _run_model_condition_guard(self) -> None:
        source_jnl = Path("D:/Projects/AbqPilot-v2/CAE_model/sanity_base/sanity_base_v01.jnl")
        source_inp = Path("D:/Projects/AbqPilot-v2/runs/stage3_9b_real_sanity_base_patch_candidate/source_sanity_base_export.inp")
        candidate = Path("D:/Projects/AbqPilot-v2/runs/stage4_3_guarded_dflux_deactivation_patch_preview/candidate_sanity_base_power_x2_stage4_dflux_deactivated_preview.inp")
        solver_inp = Path("D:/Projects/AbqPilot-v2/runs/stage4_4_dflux_deactivated_controlled_solver_validation/run_20260703_232004_870667/candidate_sanity_base_power_x2_stage4_dflux_deactivated_solver.inp")
        output = Path("D:/Projects/AbqPilot-v2/runs/stage4_5_model_condition_preservation_guard")
        result = self.controller.run_model_condition_guard(
            source_jnl=source_jnl,
            source_inp=source_inp,
            candidate_inp=candidate,
            solver_inp=solver_inp,
            output_dir=output,
            target_change="body_heat_flux_magnitude:load_body_hflux_00:step_scan_00:1e+10:2e+10",
        )
        self._handle_action_result(result, "Model Condition Preservation Guard complete")

    def _approve_dflux_guarded_solver_run(self) -> None:
        solver_run = _latest_dflux_solver_run_dir()
        if solver_run is None:
            self._set_status("No DFLUX-guarded solver run found")
            return
        phrase = simpledialog.askstring("DFLUX Solver Approval", "Enter the DFLUX-guarded solver approval phrase:", show=None)
        if not phrase:
            self._set_status("DFLUX solver approval cancelled")
            return
        result = self.controller.approve_dflux_guarded_solver_run(solver_run, phrase)
        self._handle_action_result(result, "DFLUX-guarded approval token created")

    def _run_dflux_guarded_solver(self) -> None:
        solver_run = _latest_dflux_solver_run_dir()
        if solver_run is None:
            self._set_status("No DFLUX-guarded solver run found")
            return
        confirmed = messagebox.askyesno(
            "Confirm DFLUX-Guarded Solver Run",
            "Run the approved DFLUX-deactivated single Abaqus job?\n\n"
            "The Stage 4.3 lifecycle guard and approval token must both validate.",
        )
        if not confirmed:
            self._set_status("DFLUX-guarded solver run cancelled")
            return
        result = self.controller.run_dflux_guarded_solver_approved(solver_run)
        self._handle_action_result(result, "DFLUX-guarded solver run finished")

    def _monitor_dflux_guarded_solver(self) -> None:
        solver_run = _latest_dflux_solver_run_dir()
        if solver_run is None:
            self._set_status("No DFLUX-guarded solver run found")
            return
        result = self.controller.monitor_dflux_guarded_solver_run(solver_run)
        self._handle_action_result(result, "DFLUX-guarded solver monitor complete")

    def _intake_dflux_guarded_solver_output(self) -> None:
        solver_run = _latest_dflux_solver_run_dir()
        if solver_run is None:
            self._set_status("No DFLUX-guarded solver run found")
            return
        result = self.controller.intake_dflux_guarded_solver_output(solver_run)
        self._handle_action_result(result, "DFLUX-guarded solver output intake complete")

    def _report_dflux_guarded_solver_run(self) -> None:
        solver_run = _latest_dflux_solver_run_dir()
        if solver_run is None:
            self._set_status("No DFLUX-guarded solver run found")
            return
        result = self.controller.report_dflux_guarded_solver_run(solver_run)
        self._handle_action_result(result, "DFLUX-guarded solver report complete")

    def _blocked_action(self, name: str) -> None:
        result = self.controller.blocked_action(name)
        messagebox.showwarning("Disabled", DISABLED_ACTION_MESSAGE)
        self._append_action_result(result)
        self._set_status(result["verdict"])

    def _require_task(self, action, success_message: str) -> None:
        if not self.task_dir:
            self._set_status("Load a task first")
            return
        self._handle_action_result(action(), success_message)

    def _handle_action_result(self, result: dict, success_message: str) -> None:
        self._append_action_result(result)
        if self.task_dir and Path(self.task_dir).exists():
            self.refresh()
        self._set_status(success_message if result.get("success") else result.get("verdict", "Action failed"))

    def _append_action_result(self, result: dict) -> None:
        line = f"[action] {result.get('command')}: {result.get('verdict') or result.get('status')}"
        current = self.event_text.get("1.0", "end").rstrip() if hasattr(self, "event_text") else ""
        set_text(self.event_text, (current + "\n" + line).strip())

    def _load_recent_tasks(self) -> None:
        result = self.controller.recent_tasks(self.project_root / "runs")
        self.recent_tasks = result.get("tasks", [])
        self.recent_list.delete(0, "end")
        for item in self.recent_tasks:
            self.recent_list.insert("end", f"{item.get('task_id')} [{item.get('overall_status')}]")
        self._set_status("Recent tasks loaded")

    def _set_status(self, text: str) -> None:
        self.bottom_label.configure(text=text)


def main() -> None:
    app = AbqPilotGui()
    app.mainloop()


def _latest_patch_preview_summary(task_dir: Path) -> Path | None:
    root = task_dir / "patch_previews"
    if not root.exists():
        return None
    candidates = sorted(root.glob("preview_*/patch_preview_summary.json"), key=lambda path: path.stat().st_mtime, reverse=True)
    return candidates[0] if candidates else None


def _latest_patch_preview_dir(task_dir: Path) -> Path | None:
    summary = _latest_patch_preview_summary(task_dir)
    return summary.parent if summary is not None else None


def _latest_patch_queue_workflow(task_dir: Path) -> Path | None:
    root = task_dir / "patch_queue_workflows"
    if not root.exists():
        return None
    candidates = sorted(root.glob("queue_*"), key=lambda path: path.stat().st_mtime, reverse=True)
    return candidates[0] if candidates else None


def _latest_solver_run_dir() -> Path | None:
    root = Path("D:/Projects/AbqPilot-v2/runs/stage4_0_controlled_solver_automation")
    if not root.exists():
        return None
    candidates = sorted(root.glob("run_*"), key=lambda path: path.stat().st_mtime, reverse=True)
    return candidates[0] if candidates else None


def _latest_dflux_solver_run_dir() -> Path | None:
    root = Path("D:/Projects/AbqPilot-v2/runs/stage4_4_dflux_deactivated_controlled_solver_validation")
    if not root.exists():
        return None
    candidates = sorted(root.glob("run_*"), key=lambda path: path.stat().st_mtime, reverse=True)
    return candidates[0] if candidates else None


def _latest_solver_job_name(solver_run: Path) -> str:
    preflight = solver_run / "solver_preflight_result.json"
    if preflight.exists():
        try:
            payload = json.loads(preflight.read_text(encoding="utf-8"))
            if payload.get("job_name"):
                return str(payload["job_name"])
        except json.JSONDecodeError:
            pass
    return "candidate_sanity_base_power_x2_stage4"


if __name__ == "__main__":
    main()
