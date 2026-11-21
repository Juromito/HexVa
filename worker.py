"""Background conversion worker for the Qt interface."""

import os
import tempfile
from pathlib import Path

from PySide6.QtCore import QThread, Signal
from PySide6.QtGui import QImage

from .converter import convert_to_bmp


class ConversionWorker(QThread):
    progress_changed = Signal(int)
    succeeded = Signal(dict)
    failed = Signal(str)

    def __init__(self, source: Path, output: Path, output_format: str) -> None:
        super().__init__()
        self.source = source
        self.output = output
        self.output_format = output_format

    def run(self) -> None:
        temporary_png: str | None = None
        try:
            if self.output_format == "BMP":
                result = convert_to_bmp(self.source, self.output, self.progress_changed.emit)
                result["output_size"] = result["file_size"]
                result["format"] = "BMP"
                self.succeeded.emit(result)
                return

            with tempfile.TemporaryDirectory(dir=self.output.parent, prefix=".hexva-") as working_dir:
                intermediate_bmp = Path(working_dir) / "intermediate.bmp"
                result = convert_to_bmp(
                    self.source,
                    intermediate_bmp,
                    lambda percent: self.progress_changed.emit(int(percent * 0.85)),
                )
                self.progress_changed.emit(90)

                with tempfile.NamedTemporaryFile(
                    suffix=".png", dir=self.output.parent, prefix=f".{self.output.name}.", delete=False
                ) as png_file:
                    temporary_png = png_file.name

                image = QImage(str(intermediate_bmp))
                if image.isNull():
                    raise ValueError("Could not open the temporary BMP image to create the PNG.")
                if not image.save(temporary_png, "PNG"):
                    raise OSError("Could not save the compressed PNG image.")

                result["bmp_size"] = result.pop("file_size")
                result["png_size"] = Path(temporary_png).stat().st_size
                result["output_size"] = result["png_size"]
                result["format"] = "PNG"
                os.replace(temporary_png, self.output)
                temporary_png = None
                self.progress_changed.emit(100)
            self.succeeded.emit(result)
        except Exception as error:
            self.failed.emit(str(error))
        finally:
            if temporary_png:
                try:
                    os.unlink(temporary_png)
                except OSError:
                    pass
