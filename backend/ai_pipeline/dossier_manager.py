# backend/ai_pipeline/dossier_manager.py
# Phase 09 — Dossier Lifecycle Manager
#
# Responsibilities:
#   - create_dossier()    : persist dossier + document rows to PostgreSQL
#   - process_dossier()   : background task — run each PDF through AIPipeline
#   - get_status()        : return per-document status + extraction results
#
# Design:
#   - Uses the same ThreadedConnectionPool pattern as EntityNormalizer
#   - DB unavailable → graceful degradation (pipeline still runs)
#   - Each document fails independently — one error does not abort others

import json
import logging
import os
import uuid
from typing import Optional

logger = logging.getLogger(__name__)


class DossierManager:

    def __init__(self):
        self._pool = None

        db_url = os.getenv("DATABASE_URL")
        if db_url:
            try:
                from psycopg2.pool import ThreadedConnectionPool

                self._pool = ThreadedConnectionPool(
                    minconn=1,
                    maxconn=5,
                    dsn=db_url,
                )
                logger.info("DossierManager: DB pool ready")
            except Exception as exc:
                logger.warning("DossierManager: DB unavailable: %s", exc)

        # Import lazily so the module can be imported without heavy deps
        self._pipeline = None

    def _get_pipeline(self):
        if self._pipeline is None:
            from .pipeline import get_pipeline

            self._pipeline = get_pipeline()
        return self._pipeline

    # ==================================================================
    # CREATE
    # ==================================================================

    def create_dossier(
        self,
        dossier_id: str,
        documents: list[dict],
    ) -> list[str]:
        """
        Persist dossier + document rows.
        Returns list of document_ids in insertion order.
        Falls back to synthetic UUIDs when DB is unavailable.
        """
        if self._pool is None:
            logger.warning(
                "DossierManager: no DB — synthetic IDs for dossier %s",
                dossier_id,
            )
            return [str(uuid.uuid4()) for _ in documents]

        doc_ids: list[str] = []
        conn = None
        try:
            conn = self._pool.getconn()
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO dossiers (id, status) VALUES (%s, 'pending')",
                    (dossier_id,),
                )
                for doc in documents:
                    doc_id = str(uuid.uuid4())
                    cur.execute(
                        """
                        INSERT INTO dossier_documents
                            (id, dossier_id, original_name, file_path, status)
                        VALUES (%s, %s, %s, %s, 'pending')
                        """,
                        (
                            doc_id,
                            dossier_id,
                            doc["original_name"],
                            doc["file_path"],
                        ),
                    )
                    doc_ids.append(doc_id)
            conn.commit()
        except Exception as exc:
            logger.warning("create_dossier DB error: %s", exc)
            if conn:
                try:
                    conn.rollback()
                except Exception:
                    pass
        finally:
            if conn:
                self._pool.putconn(conn)

        return doc_ids

    # ==================================================================
    # PROCESS  (runs as FastAPI BackgroundTask)
    # ==================================================================

    def process_dossier(self, dossier_id: str) -> None:
        """
        Process every pending document in the dossier through the AI pipeline.
        Called as a FastAPI background task — must never raise.
        """
        docs = self._fetch_pending_docs(dossier_id)

        self._set_dossier_status(dossier_id, "processing")

        all_ok = True
        pipeline = self._get_pipeline()

        for doc in docs:
            doc_id = doc["id"]
            pdf_path = doc["file_path"]

            self._set_document_status(doc_id, "processing")

            try:
                result = pipeline.process_document(
                    pdf_path=pdf_path,
                    document_id=doc_id,
                )
                self._save_result(
                    doc_id=doc_id,
                    document_type=result.get("document_type"),
                    extraction_json=result,
                )
                self._set_document_status(doc_id, "done")
                logger.info("DossierManager: doc %s done", doc_id)

            except Exception as exc:
                logger.exception(
                    "DossierManager: doc %s failed: %s", doc_id, exc
                )
                self._set_document_status(
                    doc_id, "error", error_message=str(exc)
                )
                all_ok = False

        self._set_dossier_status(
            dossier_id, "done" if all_ok else "error"
        )

    # ==================================================================
    # STATUS
    # ==================================================================

    def get_status(self, dossier_id: str) -> Optional[dict]:
        """
        Return dossier + per-document status.
        Returns None if dossier not found or DB unavailable.
        """
        if self._pool is None:
            return None

        conn = None
        try:
            conn = self._pool.getconn()
            with conn.cursor() as cur:

                cur.execute(
                    "SELECT id, status, created_at FROM dossiers WHERE id = %s",
                    (dossier_id,),
                )
                row = cur.fetchone()
                if row is None:
                    return None

                result = {
                    "dossier_id": str(row[0]),
                    "status": row[1],
                    "created_at": row[2].isoformat(),
                }

                cur.execute(
                    """
                    SELECT
                        id,
                        original_name,
                        document_type,
                        status,
                        error_message,
                        extraction_json
                    FROM dossier_documents
                    WHERE dossier_id = %s
                    ORDER BY created_at
                    """,
                    (dossier_id,),
                )

                result["documents"] = [
                    {
                        "document_id": str(r[0]),
                        "original_name": r[1],
                        "document_type": r[2],
                        "status": r[3],
                        "error_message": r[4],
                        "extraction_result": r[5],  # already dict via JSONB
                    }
                    for r in cur.fetchall()
                ]

                return result

        except Exception as exc:
            logger.warning("get_status DB error: %s", exc)
            return None
        finally:
            if conn:
                self._pool.putconn(conn)

    # ==================================================================
    # PRIVATE HELPERS
    # ==================================================================

    def _fetch_pending_docs(self, dossier_id: str) -> list[dict]:
        if self._pool is None:
            return []
        conn = None
        try:
            conn = self._pool.getconn()
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, file_path
                    FROM dossier_documents
                    WHERE dossier_id = %s AND status = 'pending'
                    ORDER BY created_at
                    """,
                    (dossier_id,),
                )
                return [
                    {"id": str(r[0]), "file_path": r[1]}
                    for r in cur.fetchall()
                ]
        except Exception as exc:
            logger.warning("_fetch_pending_docs: %s", exc)
            return []
        finally:
            if conn:
                self._pool.putconn(conn)

    def _set_dossier_status(self, dossier_id: str, status: str) -> None:
        self._run_sql(
            "UPDATE dossiers SET status = %s WHERE id = %s",
            (status, dossier_id),
        )

    def _set_document_status(
        self,
        doc_id: str,
        status: str,
        error_message: Optional[str] = None,
    ) -> None:
        self._run_sql(
            """
            UPDATE dossier_documents
            SET status = %s, error_message = %s, updated_at = NOW()
            WHERE id = %s
            """,
            (status, error_message, doc_id),
        )

    def _save_result(
        self,
        doc_id: str,
        document_type: Optional[str],
        extraction_json: dict,
    ) -> None:
        self._run_sql(
            """
            UPDATE dossier_documents
            SET document_type   = %s,
                extraction_json = %s,
                status          = 'done',
                updated_at      = NOW()
            WHERE id = %s
            """,
            (document_type, json.dumps(extraction_json), doc_id),
        )

    def _run_sql(self, sql: str, params: tuple) -> None:
        if self._pool is None:
            return
        conn = None
        try:
            conn = self._pool.getconn()
            with conn.cursor() as cur:
                cur.execute(sql, params)
            conn.commit()
        except Exception as exc:
            logger.warning("DossierManager SQL error: %s", exc)
            if conn:
                try:
                    conn.rollback()
                except Exception:
                    pass
        finally:
            if conn:
                self._pool.putconn(conn)
