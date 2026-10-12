# ============================================================
# CONTEXT ACTION MENU
#
# OCR selected text -> Read / Translate / Summarize
#
# AI operations run in background threads so the Tkinter
# interface never freezes during Gemini/Ollama processing.
# ============================================================

import threading
import tkinter as tk
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText


class ContextActionMenu:

    LANGUAGES = [
        "Kannada",
        "English",
        "Hindi",
        "Tamil",
        "Telugu",
        "Malayalam",
        "Marathi",
        "Bengali",
    ]

    def __init__(
        self,
        processor,
        target_language="Kannada",
    ):

        self.processor = processor

        self.target_language = (
            target_language
            if target_language in self.LANGUAGES
            else "Kannada"
        )

        self.root = None

        self.selected_text = ""

        self.result_text = None

        self.status_label = None

        self.language_box = None

        self.action_buttons = []

        self.close_button = None

        self.busy = False

        self.last_operation = ""

        self.last_result = ""

    # ========================================================
    # SHOW MENU
    # ========================================================

    def show(
        self,
        selected_text,
        ocr_confidence=0.0,
        word_count=0,
    ):

        self.selected_text = (
            selected_text or ""
        ).strip()

        if not self.selected_text:

            return {
                "success": False,
                "error": "No selected OCR text.",
                "operation": "",
                "result": "",
            }

        self.root = tk.Tk()

        self.root.title(
            "OCR Context Actions"
        )

        self.root.geometry(
            "760x600"
        )

        self.root.minsize(
            650,
            500
        )

        self.root.resizable(
            True,
            True
        )

        self.root.attributes(
            "-topmost",
            True
        )

        self._build_ui(
            ocr_confidence,
            word_count,
        )

        self.root.mainloop()

        return {
            "success": True,
            "operation": self.last_operation,
            "result": self.last_result,
        }

    # ========================================================
    # BUILD UI
    # ========================================================

    def _build_ui(
        self,
        ocr_confidence,
        word_count,
    ):

        main = ttk.Frame(
            self.root,
            padding=15,
        )

        main.pack(
            fill="both",
            expand=True,
        )

        # ----------------------------------------------------
        # Title
        # ----------------------------------------------------

        title = ttk.Label(
            main,
            text="OCR Context Actions",
            font=(
                "Segoe UI",
                18,
                "bold",
            ),
        )

        title.pack(
            anchor="w"
        )

        # ----------------------------------------------------
        # OCR information
        # ----------------------------------------------------

        info = ttk.Label(
            main,
            text=(
                f"Words: {word_count}    "
                f"OCR confidence: "
                f"{ocr_confidence:.2f}%"
            ),
            font=(
                "Segoe UI",
                10,
            ),
        )

        info.pack(
            anchor="w",
            pady=(3, 10),
        )

        # ----------------------------------------------------
        # Selected text
        # ----------------------------------------------------

        selected_label = ttk.Label(
            main,
            text="Selected Text",
            font=(
                "Segoe UI",
                11,
                "bold",
            ),
        )

        selected_label.pack(
            anchor="w"
        )

        selected_box = ScrolledText(
            main,
            height=9,
            wrap=tk.WORD,
            font=(
                "Segoe UI",
                10,
            ),
        )

        selected_box.pack(
            fill="both",
            expand=False,
            pady=(5, 12),
        )

        selected_box.insert(
            tk.END,
            self.selected_text,
        )

        selected_box.configure(
            state="disabled"
        )

        # ----------------------------------------------------
        # Action frame
        # ----------------------------------------------------

        action_frame = ttk.LabelFrame(
            main,
            text="Choose Action",
            padding=10,
        )

        action_frame.pack(
            fill="x"
        )

        # ----------------------------------------------------
        # Read
        # ----------------------------------------------------

        read_button = ttk.Button(
            action_frame,
            text="🔊 Read",
            command=self._read,
        )

        read_button.grid(
            row=0,
            column=0,
            padx=5,
            pady=5,
            sticky="ew",
        )

        self.action_buttons.append(
            read_button
        )

        # ----------------------------------------------------
        # Translate
        # ----------------------------------------------------

        translate_button = ttk.Button(
            action_frame,
            text="🌐 Translate",
            command=self._translate,
        )

        translate_button.grid(
            row=0,
            column=1,
            padx=5,
            pady=5,
            sticky="ew",
        )

        self.action_buttons.append(
            translate_button
        )

        # ----------------------------------------------------
        # Summarize
        # ----------------------------------------------------

        summarize_button = ttk.Button(
            action_frame,
            text="✨ Summarize",
            command=self._summarize,
        )

        summarize_button.grid(
            row=0,
            column=2,
            padx=5,
            pady=5,
            sticky="ew",
        )

        self.action_buttons.append(
            summarize_button
        )

        # ----------------------------------------------------
        # Language
        # ----------------------------------------------------

        language_label = ttk.Label(
            action_frame,
            text="Translation language:",
        )

        language_label.grid(
            row=1,
            column=0,
            padx=5,
            pady=(10, 5),
            sticky="w",
        )

        self.language_box = ttk.Combobox(
            action_frame,
            values=self.LANGUAGES,
            state="readonly",
            width=18,
        )

        self.language_box.set(
            self.target_language
        )

        self.language_box.grid(
            row=1,
            column=1,
            padx=5,
            pady=(10, 5),
            sticky="w",
        )

        for column in range(3):

            action_frame.columnconfigure(
                column,
                weight=1,
            )

        # ----------------------------------------------------
        # Status
        # ----------------------------------------------------

        self.status_label = ttk.Label(
            main,
            text="Select an action.",
            font=(
                "Segoe UI",
                10,
            ),
        )

        self.status_label.pack(
            anchor="w",
            pady=(12, 5),
        )

        # ----------------------------------------------------
        # Result
        # ----------------------------------------------------

        result_label = ttk.Label(
            main,
            text="Result",
            font=(
                "Segoe UI",
                11,
                "bold",
            ),
        )

        result_label.pack(
            anchor="w"
        )

        self.result_text = ScrolledText(
            main,
            height=8,
            wrap=tk.WORD,
            font=(
                "Segoe UI",
                10,
            ),
        )

        self.result_text.pack(
            fill="both",
            expand=True,
            pady=(5, 10),
        )

        # ----------------------------------------------------
        # Close
        # ----------------------------------------------------

        self.close_button = ttk.Button(
            main,
            text="Close",
            command=self._close,
        )

        self.close_button.pack(
            anchor="e"
        )

    # ========================================================
    # RUN OPERATION IN BACKGROUND
    # ========================================================

    def _run_background(
        self,
        operation,
    ):

        if self.busy:

            return

        self.busy = True

        self._set_controls(
            enabled=False
        )

        if operation == "read":

            self._set_status(
                "Reading selected text..."
            )

        elif operation == "translate":

            language = (
                self.language_box
                .get()
                .strip()
            )

            if not language:

                language = "Kannada"

            self._set_status(
                f"Translating to {language}..."
            )

        elif operation == "summarize":

            self._set_status(
                "Summarizing selected text..."
            )

        worker = threading.Thread(
            target=self._worker,
            args=(operation,),
            daemon=True,
        )

        worker.start()

    # ========================================================
    # BACKGROUND WORKER
    # ========================================================

    def _worker(
        self,
        operation,
    ):

        try:

            if operation == "read":

                result = (
                    self.processor.process_text(
                        text=self.selected_text,
                        operation="read",
                        speak=True,
                    )
                )

            elif operation == "translate":

                language = (
                    self.language_box
                    .get()
                    .strip()
                )

                if not language:

                    language = "Kannada"

                result = (
                    self.processor.process_text(
                        text=self.selected_text,
                        operation="translate",
                        target_language=language,
                        speak=True,
                    )
                )

            elif operation == "summarize":

                result = (
                    self.processor.process_text(
                        text=self.selected_text,
                        operation="summarize",
                        speak=True,
                    )
                )

            else:

                result = {
                    "success": False,
                    "operation": operation,
                    "result": "",
                    "error": (
                        "Unsupported operation."
                    ),
                }

            # ------------------------------------------------
            # Return result to Tkinter main thread
            # ------------------------------------------------

            if self.root:

                self.root.after(
                    0,
                    self._operation_finished,
                    result,
                )

        except Exception as error:

            if self.root:

                self.root.after(
                    0,
                    self._operation_finished,
                    {
                        "success": False,
                        "operation": operation,
                        "result": "",
                        "error": str(error),
                    },
                )

    # ========================================================
    # OPERATION FINISHED
    # ========================================================

    def _operation_finished(
        self,
        result,
    ):

        self.busy = False

        self._set_controls(
            enabled=True
        )

        self._show_result(
            result
        )

    # ========================================================
    # READ
    # ========================================================

    def _read(self):

        self._run_background(
            "read"
        )

    # ========================================================
    # TRANSLATE
    # ========================================================

    def _translate(self):

        self._run_background(
            "translate"
        )

    # ========================================================
    # SUMMARIZE
    # ========================================================

    def _summarize(self):

        self._run_background(
            "summarize"
        )

    # ========================================================
    # SET CONTROL STATE
    # ========================================================

    def _set_controls(
        self,
        enabled=True,
    ):

        state = (
            "normal"
            if enabled
            else "disabled"
        )

        for button in self.action_buttons:

            button.configure(
                state=state
            )

        if self.language_box:

            self.language_box.configure(
                state=(
                    "readonly"
                    if enabled
                    else "disabled"
                )
            )

        if self.close_button:

            self.close_button.configure(
                state=state
            )

    # ========================================================
    # SHOW RESULT
    # ========================================================

    def _show_result(
        self,
        result,
    ):

        success = result.get(
            "success",
            False,
        )

        operation = result.get(
            "operation",
            "",
        )

        output = result.get(
            "result",
            "",
        )

        if not success:

            error = result.get(
                "error",
                "Unknown error.",
            )

            self._set_status(
                f"Error: {error}"
            )

            self._replace_result(
                error
            )

            return

        self.last_operation = (
            operation
        )

        self.last_result = (
            output
        )

        self._set_status(
            f"{operation} completed."
        )

        self._replace_result(
            output
        )

    # ========================================================
    # REPLACE RESULT TEXT
    # ========================================================

    def _replace_result(
        self,
        text,
    ):

        self.result_text.configure(
            state="normal"
        )

        self.result_text.delete(
            "1.0",
            tk.END,
        )

        self.result_text.insert(
            tk.END,
            text or "",
        )

        self.result_text.configure(
            state="disabled"
        )

    # ========================================================
    # STATUS
    # ========================================================

    def _set_status(
        self,
        text,
    ):

        if self.status_label:

            self.status_label.configure(
                text=text
            )

            if self.root:

                self.root.update_idletasks()

    # ========================================================
    # CLOSE
    # ========================================================

    def _close(
        self
    ):

        if self.busy:

            return

        if self.root:

            self.root.destroy()