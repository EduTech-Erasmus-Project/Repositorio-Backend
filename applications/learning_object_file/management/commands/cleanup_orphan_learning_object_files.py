"""Limpia paquetes OA subidos que nunca llegaron a registrar metadata."""

import shutil
from datetime import timedelta
from pathlib import Path
from urllib.parse import unquote, urlparse

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from applications.learning_object_file.models import LearningObjectFile
from applications.learning_object_metadata.models import LearningObjectMetadata


class Command(BaseCommand):
    """Elimina `LearningObjectFile` huerfanos despues de una ventana de gracia."""

    help = (
        "Delete orphan LearningObjectFile records and their physical ZIP/catalog "
        "files when they do not have LearningObjectMetadata after a grace period."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--hours",
            type=int,
            default=24,
            help="Minimum age in hours before an orphan file can be deleted.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Only report candidates without deleting files or database rows.",
        )
        parser.add_argument(
            "--include-physical-orphans",
            action="store_true",
            help=(
                "Also clean old ZIP files in media/oazip and top-level folders in "
                "media/catalog that are not referenced by any LearningObjectFile."
            ),
        )
        parser.add_argument(
            "--summary-only",
            action="store_true",
            help="Only print final summaries, useful before cleaning many files.",
        )
        parser.add_argument(
            "--include-model-file-orphans",
            action="store_true",
            help=(
                "Also clean old files in media/avatar, media/sourceFile and "
                "media/profile that are not referenced by model FileField/ImageField values."
            ),
        )

    def handle(self, *args, **options):
        hours = options["hours"]
        dry_run = options["dry_run"]
        include_physical_orphans = options["include_physical_orphans"]
        include_model_file_orphans = options["include_model_file_orphans"]
        summary_only = options["summary_only"]
        if hours < 1:
            raise CommandError("--hours must be greater than or equal to 1")

        cutoff = timezone.now() - timedelta(hours=hours)
        media_root = Path(settings.MEDIA_ROOT).resolve()
        oazip_root = (media_root / "oazip").resolve()
        catalog_root = (media_root / "catalog").resolve()

        candidates = LearningObjectFile.objects.filter(
            metadata_learning_object__isnull=True,
            created__lt=cutoff,
        ).order_by("id")

        stats = {
            "found": candidates.count(),
            "deleted": 0,
            "skipped": 0,
            "errors": 0,
        }

        for learning_object_file in candidates:
            try:
                if self._has_metadata(learning_object_file):
                    stats["skipped"] += 1
                    self._write_skip(learning_object_file, "metadata exists", summary_only)
                    continue

                zip_path = self._resolve_zip_path(learning_object_file, media_root)
                catalog_path = self._resolve_catalog_path(learning_object_file)

                zip_safe = self._is_safe_child(zip_path, oazip_root)
                catalog_safe = self._is_safe_child(catalog_path, catalog_root)

                if not zip_safe or not catalog_safe:
                    stats["skipped"] += 1
                    self._write_skip(learning_object_file, "unsafe path", summary_only)
                    continue

                if dry_run:
                    stats["skipped"] += 1
                    if not summary_only:
                        self.stdout.write(
                            f"[dry-run] orphan LearningObjectFile {learning_object_file.id}: "
                            f"zip={zip_path} catalog={catalog_path}"
                        )
                    continue

                self._delete_file(zip_path)
                self._delete_directory(catalog_path)
                learning_object_file.delete()
                stats["deleted"] += 1
                if not summary_only:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"Deleted orphan LearningObjectFile {learning_object_file.id}"
                        )
                    )
            except Exception as exc:  # noqa: BLE001 - management command must continue.
                stats["errors"] += 1
                self.stderr.write(
                    f"Error cleaning LearningObjectFile {learning_object_file.id}: {exc}"
                )

        self.stdout.write(
            "Database orphan cleanup summary: "
            f"found={stats['found']} "
            f"deleted={stats['deleted']} "
            f"skipped={stats['skipped']} "
            f"errors={stats['errors']}"
        )

        if include_physical_orphans:
            self._cleanup_physical_orphans(
                cutoff,
                media_root,
                oazip_root,
                catalog_root,
                dry_run,
                summary_only,
            )

        if include_model_file_orphans:
            self._cleanup_model_file_orphans(
                cutoff,
                media_root,
                dry_run,
                summary_only,
            )

    def _has_metadata(self, learning_object_file):
        """Revalida la relacion antes de borrar para evitar carreras."""

        return LearningObjectFile.objects.filter(
            pk=learning_object_file.pk,
            metadata_learning_object__isnull=False,
        ).exists()

    def _resolve_zip_path(self, learning_object_file, media_root):
        """Obtiene la ruta local del ZIP desde el storage o desde `file.name`."""

        try:
            return Path(learning_object_file.file.path).resolve()
        except (NotImplementedError, ValueError):
            return (media_root / learning_object_file.file.name).resolve()

    def _resolve_catalog_path(self, learning_object_file):
        if not learning_object_file.path_origin:
            raise ValueError("path_origin is empty")
        return Path(learning_object_file.path_origin).resolve()

    def _is_safe_child(self, path, expected_parent):
        """Evita borrar `media`, `catalog`, `oazip` o rutas externas."""

        if path == expected_parent:
            return False
        try:
            path.relative_to(expected_parent)
        except ValueError:
            return False
        return True

    def _delete_file(self, path):
        if path.exists():
            path.unlink()

    def _delete_directory(self, path):
        if path.exists():
            shutil.rmtree(path)

    def _write_skip(self, learning_object_file, reason, summary_only=False):
        if summary_only:
            return
        self.stdout.write(
            f"Skipped LearningObjectFile {learning_object_file.id}: {reason}"
        )

    def _cleanup_physical_orphans(
        self,
        cutoff,
        media_root,
        oazip_root,
        catalog_root,
        dry_run,
        summary_only,
    ):
        """Limpia ZIPs y carpetas fisicas que ya no tienen registro en base."""

        referenced_zip_paths, referenced_catalog_paths = self._collect_referenced_paths(
            media_root,
            oazip_root,
            catalog_root,
        )
        stats = {
            "found": 0,
            "deleted": 0,
            "skipped": 0,
            "errors": 0,
        }
        zip_stats = {
            "found": 0,
            "deleted": 0,
            "skipped": 0,
            "errors": 0,
        }
        catalog_stats = {
            "found": 0,
            "deleted": 0,
            "skipped": 0,
            "errors": 0,
        }

        for zip_path in self._iter_physical_zip_orphans(
            oazip_root,
            referenced_zip_paths,
            cutoff,
        ):
            stats["found"] += 1
            zip_stats["found"] += 1
            try:
                if not self._is_direct_child(zip_path, oazip_root):
                    stats["skipped"] += 1
                    zip_stats["skipped"] += 1
                    if not summary_only:
                        self.stdout.write(
                            f"Skipped physical ZIP outside direct root: {zip_path}"
                        )
                    continue
                if dry_run:
                    stats["skipped"] += 1
                    zip_stats["skipped"] += 1
                    if not summary_only:
                        self.stdout.write(f"[dry-run] physical orphan ZIP: {zip_path}")
                    continue
                self._delete_file(zip_path)
                stats["deleted"] += 1
                zip_stats["deleted"] += 1
                if not summary_only:
                    self.stdout.write(
                        self.style.SUCCESS(f"Deleted physical orphan ZIP: {zip_path}")
                    )
            except Exception as exc:  # noqa: BLE001 - management command must continue.
                stats["errors"] += 1
                zip_stats["errors"] += 1
                self.stderr.write(f"Error cleaning physical ZIP {zip_path}: {exc}")

        for catalog_path in self._iter_physical_catalog_orphans(
            catalog_root,
            referenced_catalog_paths,
            cutoff,
        ):
            stats["found"] += 1
            catalog_stats["found"] += 1
            try:
                if not self._is_direct_child(catalog_path, catalog_root):
                    stats["skipped"] += 1
                    catalog_stats["skipped"] += 1
                    if not summary_only:
                        self.stdout.write(
                            f"Skipped physical catalog outside direct root: {catalog_path}"
                        )
                    continue
                if dry_run:
                    stats["skipped"] += 1
                    catalog_stats["skipped"] += 1
                    if not summary_only:
                        self.stdout.write(
                            f"[dry-run] physical orphan catalog: {catalog_path}"
                        )
                    continue
                self._delete_directory(catalog_path)
                stats["deleted"] += 1
                catalog_stats["deleted"] += 1
                if not summary_only:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"Deleted physical orphan catalog: {catalog_path}"
                        )
                    )
            except Exception as exc:  # noqa: BLE001 - management command must continue.
                stats["errors"] += 1
                catalog_stats["errors"] += 1
                self.stderr.write(f"Error cleaning physical catalog {catalog_path}: {exc}")

        self.stdout.write(
            "Physical ZIP orphan cleanup summary: "
            f"found={zip_stats['found']} "
            f"deleted={zip_stats['deleted']} "
            f"skipped={zip_stats['skipped']} "
            f"errors={zip_stats['errors']}"
        )
        self.stdout.write(
            "Physical catalog orphan cleanup summary: "
            f"found={catalog_stats['found']} "
            f"deleted={catalog_stats['deleted']} "
            f"skipped={catalog_stats['skipped']} "
            f"errors={catalog_stats['errors']}"
        )
        self.stdout.write(
            "Physical orphan cleanup summary: "
            f"found={stats['found']} "
            f"deleted={stats['deleted']} "
            f"skipped={stats['skipped']} "
            f"errors={stats['errors']}"
        )

    def _collect_referenced_paths(self, media_root, oazip_root, catalog_root):
        """Obtiene ZIPs y carpetas de catalogo todavia referenciados en base."""

        referenced_zip_paths = set()
        referenced_catalog_paths = set()

        for learning_object_file in LearningObjectFile.objects.all():
            try:
                zip_path = self._resolve_zip_path(learning_object_file, media_root)
                if self._is_safe_child(zip_path, oazip_root):
                    referenced_zip_paths.add(zip_path)
            except Exception:
                pass

            try:
                catalog_path = self._resolve_catalog_path(learning_object_file)
                if self._is_safe_child(catalog_path, catalog_root):
                    referenced_catalog_paths.add(catalog_path)
            except Exception:
                pass

            try:
                catalog_path = self._resolve_catalog_path_from_url(
                    learning_object_file.url,
                    catalog_root,
                )
                if self._is_safe_child(catalog_path, catalog_root):
                    referenced_catalog_paths.add(catalog_path)
            except Exception:
                pass

        return referenced_zip_paths, referenced_catalog_paths

    def _resolve_catalog_path_from_url(self, url, catalog_root):
        """Obtiene la carpeta de catalogo desde la URL publica del OA."""

        if not url:
            raise ValueError("url is empty")

        parsed_path = unquote(urlparse(url).path)
        marker = f"{settings.MEDIA_URL.rstrip('/')}/catalog/"
        marker_index = parsed_path.find(marker)
        if marker_index == -1:
            raise ValueError("url does not reference media/catalog")

        relative_catalog_path = parsed_path[marker_index + len(marker):].lstrip("/")
        catalog_folder = relative_catalog_path.split("/", 1)[0]
        if not catalog_folder:
            raise ValueError("url does not include catalog folder")

        return (catalog_root / catalog_folder).resolve()

    def _iter_physical_zip_orphans(self, oazip_root, referenced_zip_paths, cutoff):
        """Lista ZIPs fisicos directos no referenciados y antiguos."""

        if not oazip_root.exists():
            return

        for path in oazip_root.iterdir():
            if not path.is_file():
                continue
            resolved_path = path.resolve()
            if resolved_path in referenced_zip_paths:
                continue
            if not self._is_path_older_than(resolved_path, cutoff):
                continue
            yield resolved_path

    def _iter_physical_catalog_orphans(
        self,
        catalog_root,
        referenced_catalog_paths,
        cutoff,
    ):
        """Lista carpetas directas de catalogo no referenciadas y antiguas."""

        if not catalog_root.exists():
            return

        for path in catalog_root.iterdir():
            if not path.is_dir():
                continue
            resolved_path = path.resolve()
            if resolved_path in referenced_catalog_paths:
                continue
            if not self._is_path_older_than(resolved_path, cutoff):
                continue
            yield resolved_path

    def _is_path_older_than(self, path, cutoff):
        return path.stat().st_mtime < cutoff.timestamp()

    def _is_direct_child(self, path, expected_parent):
        if not self._is_safe_child(path, expected_parent):
            return False
        return path.parent == expected_parent

    def _cleanup_model_file_orphans(self, cutoff, media_root, dry_run, summary_only):
        """Limpia archivos de campos FileField/ImageField sin referencia en base."""

        cleanup_specs = [
            (
                "avatar",
                media_root / "avatar",
                LearningObjectMetadata.objects.exclude(avatar="").values_list(
                    "avatar",
                    flat=True,
                ),
            ),
            (
                "sourceFile",
                media_root / "sourceFile",
                LearningObjectMetadata.objects.exclude(source_file="")
                .exclude(source_file__isnull=True)
                .values_list("source_file", flat=True),
            ),
            (
                "profile",
                media_root / "profile",
                get_user_model()
                .objects.exclude(image="")
                .exclude(image__isnull=True)
                .values_list("image", flat=True),
            ),
        ]

        total_stats = {
            "found": 0,
            "deleted": 0,
            "skipped": 0,
            "errors": 0,
        }

        for label, root, referenced_values in cleanup_specs:
            root = root.resolve()
            referenced_paths = self._collect_model_file_references(
                media_root,
                root,
                referenced_values,
            )
            stats = self._cleanup_direct_file_orphans(
                label,
                root,
                referenced_paths,
                cutoff,
                dry_run,
                summary_only,
            )
            for key in total_stats:
                total_stats[key] += stats[key]

        self.stdout.write(
            "Model file orphan cleanup summary: "
            f"found={total_stats['found']} "
            f"deleted={total_stats['deleted']} "
            f"skipped={total_stats['skipped']} "
            f"errors={total_stats['errors']}"
        )

    def _collect_model_file_references(self, media_root, expected_root, referenced_values):
        referenced_paths = set()

        for value in referenced_values:
            if not value:
                continue
            path = (media_root / str(value)).resolve()
            if self._is_safe_child(path, expected_root):
                referenced_paths.add(path)

        return referenced_paths

    def _cleanup_direct_file_orphans(
        self,
        label,
        root,
        referenced_paths,
        cutoff,
        dry_run,
        summary_only,
    ):
        stats = {
            "found": 0,
            "deleted": 0,
            "skipped": 0,
            "errors": 0,
        }

        if not root.exists():
            self.stdout.write(
                f"Model file orphan cleanup summary for {label}: "
                "found=0 deleted=0 skipped=0 errors=0"
            )
            return stats

        for path in root.iterdir():
            if not path.is_file():
                continue
            resolved_path = path.resolve()
            if resolved_path in referenced_paths:
                continue
            if not self._is_path_older_than(resolved_path, cutoff):
                continue

            stats["found"] += 1
            try:
                if not self._is_direct_child(resolved_path, root):
                    stats["skipped"] += 1
                    if not summary_only:
                        self.stdout.write(
                            f"Skipped {label} file outside direct root: {resolved_path}"
                        )
                    continue
                if dry_run:
                    stats["skipped"] += 1
                    if not summary_only:
                        self.stdout.write(
                            f"[dry-run] model file orphan {label}: {resolved_path}"
                        )
                    continue
                self._delete_file(resolved_path)
                stats["deleted"] += 1
                if not summary_only:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"Deleted model file orphan {label}: {resolved_path}"
                        )
                    )
            except Exception as exc:  # noqa: BLE001 - management command must continue.
                stats["errors"] += 1
                self.stderr.write(f"Error cleaning model file {resolved_path}: {exc}")

        self.stdout.write(
            f"Model file orphan cleanup summary for {label}: "
            f"found={stats['found']} "
            f"deleted={stats['deleted']} "
            f"skipped={stats['skipped']} "
            f"errors={stats['errors']}"
        )
        return stats
