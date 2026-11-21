"""Main window and user interactions for HexVa."""

from pathlib import Path

from PySide6.QtCore import QSettings, QSize, Qt, QUrl
from PySide6.QtGui import QDesktopServices, QIcon, QImageReader, QPalette, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from .worker import ConversionWorker
from .resources import APP_ICON_PATH


class HexVaWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("HexVa")
        self.setWindowIcon(QIcon(str(APP_ICON_PATH)))
        self.setMinimumSize(840, 560)
        self.resize(1020, 650)
        self.worker: ConversionWorker | None = None
        self.preview_pixmap: QPixmap | None = None
        self.settings = QSettings("Juromito", "HexVa")
        self._build_ui()
        self._load_settings()

    def _build_ui(self) -> None:
        page = QWidget()
        page.setObjectName("page")
        self.setCentralWidget(page)
        layout = QVBoxLayout(page)
        layout.setContentsMargins(42, 32, 42, 28)
        layout.setSpacing(0)

        header = QHBoxLayout()
        logo = QLabel()
        logo_pixmap = QPixmap(str(APP_ICON_PATH))
        if not logo_pixmap.isNull():
            logo.setPixmap(
                logo_pixmap.scaled(
                    32,
                    32,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )
            logo.setFixedSize(32, 32)
            header.addWidget(logo)
        brand = QLabel("HexVa")
        brand.setObjectName("brand")
        header.addWidget(brand)
        header.addStretch(1)
        self.github_button = QPushButton("View on GitHub")
        self.github_button.setObjectName("secondaryButton")
        self.github_button.setToolTip("Open github.com/Juromito/HexVa")
        self.github_button.clicked.connect(self._open_github)
        header.addWidget(self.github_button)
        layout.addLayout(header)

        title = QLabel("File converter")
        title.setObjectName("title")
        layout.addWidget(title)

        self.subtitle = QLabel()
        self.subtitle.setObjectName("subtitle")
        layout.addWidget(self.subtitle)
        layout.addSpacing(28)

        options = QHBoxLayout()
        options.setSpacing(10)
        theme_label = QLabel("Theme")
        theme_label.setObjectName("fieldLabel")
        options.addWidget(theme_label)
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["System", "Light", "Dark"])
        self.theme_combo.setFixedWidth(132)
        options.addWidget(self.theme_combo)
        options.addSpacing(16)
        format_label = QLabel("Format")
        format_label.setObjectName("fieldLabel")
        options.addWidget(format_label)
        self.format_combo = QComboBox()
        self.format_combo.addItems(["PNG", "BMP"])
        self.format_combo.setFixedWidth(110)
        options.addWidget(self.format_combo)
        options.addStretch(1)
        layout.addLayout(options)
        layout.addSpacing(18)

        content = QHBoxLayout()
        content.setSpacing(20)
        layout.addLayout(content, 1)

        left_column = QVBoxLayout()
        left_column.setSpacing(0)
        content.addLayout(left_column, 3)

        card = QFrame()
        card.setObjectName("card")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(22, 22, 22, 22)
        card_layout.setSpacing(10)

        source_label = QLabel("Source file")
        source_label.setObjectName("fieldLabel")
        card_layout.addWidget(source_label)
        source_row = QHBoxLayout()
        source_row.setSpacing(10)
        self.source_input = QLineEdit()
        self.source_input.setPlaceholderText("Select a file to convert")
        self.source_input.textChanged.connect(self._source_edited)
        self.source_button = QPushButton("Browse…")
        self.source_button.setObjectName("secondaryButton")
        self.source_button.clicked.connect(self._choose_source)
        source_row.addWidget(self.source_input, 1)
        source_row.addWidget(self.source_button)
        card_layout.addLayout(source_row)

        card_layout.addSpacing(8)
        self.output_label = QLabel("Save PNG to")
        self.output_label.setObjectName("fieldLabel")
        card_layout.addWidget(self.output_label)
        output_row = QHBoxLayout()
        output_row.setSpacing(10)
        self.output_input = QLineEdit()
        self.output_input.setPlaceholderText("Choose where to save the PNG image")
        self.output_button = QPushButton("Choose…")
        self.output_button.setObjectName("secondaryButton")
        self.output_button.clicked.connect(self._choose_output)
        output_row.addWidget(self.output_input, 1)
        output_row.addWidget(self.output_button)
        card_layout.addLayout(output_row)
        left_column.addWidget(card)

        self.hint = QLabel()
        self.hint.setObjectName("hint")
        self.hint.setWordWrap(True)
        left_column.addWidget(self.hint)
        left_column.addSpacing(18)

        self.convert_button = QPushButton()
        self.convert_button.setObjectName("primaryButton")
        self.convert_button.setMinimumHeight(48)
        self.convert_button.clicked.connect(self._start_conversion)
        left_column.addWidget(self.convert_button, alignment=Qt.AlignmentFlag.AlignLeft)
        left_column.addStretch(1)

        preview_card = QFrame()
        preview_card.setObjectName("previewCard")
        preview_layout = QVBoxLayout(preview_card)
        preview_layout.setContentsMargins(16, 16, 16, 16)
        preview_layout.setSpacing(10)
        preview_title = QLabel("Preview")
        preview_title.setObjectName("fieldLabel")
        preview_layout.addWidget(preview_title)
        self.preview = QLabel("The image will appear here")
        self.preview.setObjectName("preview")
        self.preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview.setMinimumSize(260, 280)
        self.preview.setWordWrap(True)
        preview_layout.addWidget(self.preview, 1)
        self.preview_details = QLabel("PNG preview")
        self.preview_details.setObjectName("previewDetails")
        self.preview_details.setAlignment(Qt.AlignmentFlag.AlignCenter)
        preview_layout.addWidget(self.preview_details)
        content.addWidget(preview_card, 2)

        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setTextVisible(False)
        self.progress.setFixedHeight(6)
        self.progress.hide()
        layout.addSpacing(15)
        layout.addWidget(self.progress)

        self.status = QLabel("Ready to convert.")
        self.status.setObjectName("status")
        self.status.setWordWrap(True)
        layout.addSpacing(10)
        layout.addWidget(self.status)
        layout.addSpacing(18)

        footer = QLabel("Files are processed locally on this computer.")
        footer.setObjectName("footer")
        layout.addWidget(footer)

    def _apply_style(self) -> None:
        selected_theme = self.theme_combo.currentText()
        if selected_theme == "System":
            window_color = QApplication.palette().color(QPalette.ColorRole.Window)
            selected_theme = "Dark" if window_color.lightnessF() < 0.5 else "Light"

        if selected_theme == "Light":
            colors = {
                "page": "#f4f6f8", "text": "#202833", "title": "#202833", "sub": "#5e6875",
                "card": "#ffffff", "border": "#d9dfe6", "label": "#46515e", "input": "#ffffff",
                "input_border": "#cbd3dc", "secondary": "#f0f2f5", "secondary_hover": "#e5e9ee",
                "secondary_text": "#26313d", "hint": "#5e6875", "preview": "#f8f9fa",
                "preview_text": "#687482", "status": "#35414e", "footer": "#707b87", "progress": "#e2e6eb",
            }
        else:
            colors = {
                "page": "#20252b", "text": "#e8ebee", "title": "#f0f2f4", "sub": "#abb3bc",
                "card": "#292f36", "border": "#3b434c", "label": "#c4cbd2", "input": "#22282e",
                "input_border": "#46505a", "secondary": "#343c44", "secondary_hover": "#414b55",
                "secondary_text": "#e4e8ec", "hint": "#aab3bc", "preview": "#22282e",
                "preview_text": "#aab3bc", "status": "#cbd1d7", "footer": "#939da7", "progress": "#343c44",
            }

        self.setStyleSheet(
            f"""
            QWidget#page {{ background: {colors['page']}; color: {colors['text']}; font-size: 12px; }}
            QLabel#brand {{ color: {colors['title']}; font-size: 15px; font-weight: 600; }}
            QLabel#title {{ color: {colors['title']}; font-size: 25px; font-weight: 600; margin-top: 8px; }}
            QLabel#subtitle {{ color: {colors['sub']}; font-size: 13px; margin-top: 5px; }}
            QFrame#card, QFrame#previewCard {{ background: {colors['card']}; border: 1px solid {colors['border']}; border-radius: 6px; }}
            QLabel#fieldLabel {{ color: {colors['label']}; font-size: 11px; font-weight: 600; }}
            QLineEdit, QComboBox {{ background: {colors['input']}; color: {colors['text']}; border: 1px solid {colors['input_border']}; border-radius: 5px; padding: 9px 10px; selection-background-color: #376b96; }}
            QLineEdit:focus, QComboBox:focus {{ border: 1px solid #5b89b0; }}
            QComboBox QAbstractItemView {{ background: {colors['card']}; color: {colors['text']}; selection-background-color: #376b96; }}
            QPushButton#secondaryButton {{ background: {colors['secondary']}; color: {colors['secondary_text']}; border: 1px solid {colors['border']}; border-radius: 5px; padding: 9px 12px; }}
            QPushButton#secondaryButton:hover {{ background: {colors['secondary_hover']}; }}
            QPushButton#primaryButton {{ background: #376b96; color: #ffffff; border: 0; border-radius: 5px; padding: 0 18px; font-size: 12px; font-weight: 600; }}
            QPushButton#primaryButton:hover {{ background: #2f5d83; }}
            QPushButton#primaryButton:disabled {{ background: #677786; color: #e6e9ec; }}
            QLabel#hint {{ color: {colors['hint']}; font-size: 11px; margin-top: 12px; }}
            QLabel#preview {{ background: {colors['preview']}; color: {colors['preview_text']}; border: 1px solid {colors['border']}; border-radius: 5px; font-size: 12px; }}
            QLabel#previewDetails {{ color: {colors['hint']}; font-size: 11px; }}
            QLabel#status {{ color: {colors['status']}; font-size: 11px; }}
            QLabel#footer {{ color: {colors['footer']}; font-size: 10px; }}
            QProgressBar {{ background: {colors['progress']}; border: 0; border-radius: 2px; }}
            QProgressBar::chunk {{ background: #4f7da3; border-radius: 2px; }}
            """
        )

    def _load_settings(self) -> None:
        theme = self.settings.value("theme", "System")
        format_name = self.settings.value("format", "PNG")
        theme_index = self.theme_combo.findText(theme)
        format_index = self.format_combo.findText(format_name)
        self.theme_combo.setCurrentIndex(theme_index if theme_index >= 0 else 0)
        self.format_combo.setCurrentIndex(format_index if format_index >= 0 else 0)
        self.theme_combo.currentTextChanged.connect(self._theme_changed)
        self.format_combo.currentTextChanged.connect(self._format_changed)
        self._format_changed(self.format_combo.currentText())
        self._apply_style()

    def _theme_changed(self, theme: str) -> None:
        self.settings.setValue("theme", theme)
        self._apply_style()

    def _format_changed(self, format_name: str) -> None:
        self.settings.setValue("format", format_name)
        self.output_label.setText(f"Save {format_name} to")
        self.output_input.setPlaceholderText(f"Choose where to save the {format_name} image")
        self.convert_button.setText(f"Convert and save {format_name}")
        self.preview_details.setText(f"{format_name} preview")
        if format_name == "PNG":
            self.hint.setText("PNG preserves pixel data losslessly; file size depends on the source data.")
            self.subtitle.setText("Turn any file into a losslessly compressed PNG image.")
        else:
            self.hint.setText("BMP stores pixels without compression and usually takes more space.")
            self.subtitle.setText("Turn any file into a 24-bit BMP image.")
        output_text = self.output_input.text().strip()
        if output_text:
            self.output_input.setText(str(Path(output_text).with_suffix(f".{format_name.lower()}")))

    def _open_github(self) -> None:
        QDesktopServices.openUrl(QUrl("https://github.com/Juromito/HexVa"))

    def _source_edited(self, value: str) -> None:
        if value.strip():
            source = Path(value.strip()).expanduser()
            if not self.output_input.text().strip():
                self.output_input.setText(str(self._suggested_output(source)))

    def _choose_source(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Choose source file", "", "All files (*)")
        if path:
            self.source_input.setText(path)
            self.output_input.setText(str(self._suggested_output(Path(path))))

    def _choose_output(self) -> None:
        source = self.source_input.text().strip()
        initial = self.output_input.text().strip()
        if not initial and source:
            initial = str(self._suggested_output(Path(source).expanduser()))
        format_name = self.format_combo.currentText()
        path, _ = QFileDialog.getSaveFileName(
            self,
            f"Save {format_name} image",
            initial or f"image{self._selected_suffix()}",
            f"{format_name} image (*.{format_name.lower()})",
        )
        if path:
            output = Path(path)
            if output.suffix.lower() != self._selected_suffix():
                output = output.with_suffix(self._selected_suffix())
            self.output_input.setText(str(output))

    def _selected_suffix(self) -> str:
        return ".png" if self.format_combo.currentText() == "PNG" else ".bmp"

    def _suggested_output(self, source: Path) -> Path:
        suffix = self._selected_suffix()
        if source.suffix.lower() == suffix:
            return source.with_name(f"{source.stem}-hexva{suffix}")
        return source.with_suffix(suffix)

    def _start_conversion(self) -> None:
        source_text = self.source_input.text().strip()
        output_text = self.output_input.text().strip()
        if not source_text:
            QMessageBox.warning(self, "Source file required", "Select a source file first.")
            return
        if not output_text:
            self._choose_output()
            output_text = self.output_input.text().strip()
            if not output_text:
                return

        source = Path(source_text).expanduser()
        output = Path(output_text).expanduser()
        output_format = self.format_combo.currentText()
        if output.suffix.lower() != self._selected_suffix():
            output = output.with_suffix(self._selected_suffix())
            self.output_input.setText(str(output))
        if source.resolve() == output.resolve():
            QMessageBox.warning(self, "Invalid destination", "The destination must be different from the source file.")
            return
        if output.exists():
            answer = QMessageBox.question(
                self,
                "Replace existing file?",
                f"A file already exists at this location:\n{output}\n\nDo you want to replace it?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if answer != QMessageBox.StandardButton.Yes:
                return

        self.convert_button.setEnabled(False)
        self.source_button.setEnabled(False)
        self.output_button.setEnabled(False)
        self.progress.setValue(0)
        self.progress.show()
        self.status.setText("Preparing conversion…")

        self.worker = ConversionWorker(source, output, output_format)
        self.worker.progress_changed.connect(self._update_progress)
        self.worker.succeeded.connect(self._conversion_succeeded)
        self.worker.failed.connect(self._conversion_failed)
        self.worker.finished.connect(self._worker_finished)
        self.source_input.setEnabled(False)
        self.output_input.setEnabled(False)
        self.worker.start()

    def _update_progress(self, value: int) -> None:
        self.progress.setValue(value)
        self.status.setText(f"Converting… {value}%")

    def _conversion_succeeded(self, details: dict) -> None:
        self._finish_conversion()
        output_name = str(self.worker.output) if self.worker else self.output_input.text().strip()
        self._load_preview(Path(output_name))
        self.status.setText(
            f"{details['format']} created: {details['width']} × {details['height']} px · "
            f"{details['output_size']:,} bytes".replace(",", " ")
        )
        QMessageBox.information(
            self,
            "Conversion complete",
            f"{details['format']} image saved to:\n{output_name}",
        )

    def _load_preview(self, path: Path) -> None:
        reader = QImageReader(str(path))
        reader.setAutoTransform(True)
        original_size = reader.size()
        if original_size.isValid():
            target_size = QSize(max(1, self.preview.width() - 20), max(1, self.preview.height() - 20))
            reader.setScaledSize(original_size.scaled(target_size, Qt.AspectRatioMode.KeepAspectRatio))
        image = reader.read()
        if image.isNull():
            self.preview_pixmap = None
            self.preview.setPixmap(QPixmap())
            self.preview.setText("Could not load\nimage preview")
            self.preview_details.setText(f"{path.suffix.lstrip('.').upper()} saved to the selected location")
            return
        self.preview_pixmap = QPixmap.fromImage(image)
        self.preview.setPixmap(
            self.preview_pixmap.scaled(
                self.preview.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        )
        self.preview_details.setText(f"{original_size.width()} × {original_size.height()} px")

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        if self.preview_pixmap:
            self.preview.setPixmap(
                self.preview_pixmap.scaled(
                    self.preview.size(),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )

    def _conversion_failed(self, error: str) -> None:
        self._finish_conversion()
        self.status.setText("Conversion failed.")
        QMessageBox.critical(self, "Conversion failed", error)

    def _finish_conversion(self) -> None:
        self.convert_button.setEnabled(True)
        self.source_button.setEnabled(True)
        self.output_button.setEnabled(True)
        self.source_input.setEnabled(True)
        self.output_input.setEnabled(True)
        self.progress.hide()

    def _worker_finished(self) -> None:
        self.worker = None
