import {useEffect, useState} from "react";
import {Link} from "react-router-dom";
import {Pencil, Trash2} from "lucide-react";
import type {AppConfig} from "../models/config.ts";
import {deleteWorkbook as removeWorkbook, listWorkbooks, uploadWorkbook as importWorkbook, type Workbook} from "../api.ts";
import UploadWorkbook from "../components/UploadWorkbook.tsx";
import styles from "./Home.module.css";

export default function Home({config}: {config: AppConfig}) {
    const [workbooks, setWorkbooks] = useState<Workbook[]>([]);
    const [operationStatus, setOperationStatus] = useState("");
    const [pendingDelete, setPendingDelete] = useState<string | null>(null);

    async function loadWorkbooks() {
        try {
            setWorkbooks(await listWorkbooks());
        } catch {
            setOperationStatus("Could not load workbooks.");
        }
    }

    useEffect(() => {
        void loadWorkbooks();
    }, []);

    async function deleteWorkbook(name: string) {
        try {
            await removeWorkbook(name);
            setOperationStatus("Workbook deleted.");
            setPendingDelete(null);
            await loadWorkbooks();
        } catch {
            setOperationStatus("Could not delete workbook.");
        }
    }

    async function uploadWorkbook(formData: FormData, reset: () => void) {
        setOperationStatus("Uploading...");
        try {
            await importWorkbook(formData);
            setOperationStatus("Workbook imported.");
            reset();
            await loadWorkbooks();
            return;
        } catch (error) {
            setOperationStatus(error instanceof Error ? error.message : "Could not import workbook.");
        }
    }

    const completionLabel = (workbook: Workbook): string => {
        const complete = workbook.recordCount - workbook.unfilledRecordCount;
        return `${complete.toLocaleString()} / ${workbook.recordCount.toLocaleString()} complete`;
    };

    return (
        <>
            <header className={styles.pageHeader}>
                <div className={styles.headingRow}>
                    <div>
                        <p className={styles.eyebrow}>Workspace</p>
                        <h1>Primary study lists</h1>
                        {config.user && <p className={styles.greeting}>Welcome, {config.user.display_name || config.user.email}</p>}
                    </div>
                </div>
                <UploadWorkbook config={config} onUpload={uploadWorkbook}/>
                <p id="operation-status" className={styles.status} role="status">{operationStatus}</p>
            </header>
            <main className={styles.listSection}>
                <div className={styles.listHeader}>
                    <div>
                        <p className={styles.eyebrow}>Your surveys</p>
                        <h2>Continue where you left off</h2>
                    </div>
                    <span className={styles.listCount}>{workbooks.length} {workbooks.length === 1 ? "survey" : "surveys"}</span>
                </div>
                <div className={styles.tableShell}>
                    <table className={styles.table}>
                        <thead><tr><th>File name</th><th>Worksheet</th><th>Completion</th><th><span className={styles.srOnly}>Actions</span></th></tr></thead>
                        <tbody id="workbook-list">
                        {workbooks.map(workbook => (
                            <tr key={workbook.name}>
                                <td className={styles.fileName}>{workbook.name}</td>
                                <td className={styles.worksheet}>{workbook.worksheetName}</td>
                                <td>
                                    <div className={styles.progressLabel}>
                                        <span>{completionLabel(workbook)}</span>
                                        <span>{workbook.unfilledRecordCount.toLocaleString()} remaining</span>
                                    </div>
                                    <progress className={styles.progress} max={workbook.recordCount} value={workbook.recordCount - workbook.unfilledRecordCount}
                                              aria-label={`Completion for ${workbook.name}`}/>
                                </td>
                                <td className={styles.actions}>
                                    <Link className={styles.iconButton} to={`/evidence/${encodeURIComponent(workbook.name)}`} aria-label={`Edit ${workbook.name}`} title="Edit survey">
                                        <Pencil aria-hidden="true" size={16}/>
                                    </Link>
                                    {pendingDelete === workbook.name ? <span className={styles.confirmation}>
                                        <span>Delete?</span>
                                        <button className={styles.confirmButton} type="button" onClick={() => void deleteWorkbook(workbook.name)}>Yes</button>
                                        <button className={styles.cancelButton} type="button" onClick={() => setPendingDelete(null)}>No</button>
                                    </span> : <button className={`${styles.iconButton} ${styles.deleteButton}`} type="button" onClick={() => setPendingDelete(workbook.name)} aria-label={`Delete ${workbook.name}`} title="Delete survey">
                                        <Trash2 aria-hidden="true" size={16}/>
                                    </button>}
                                </td>
                            </tr>
                        ))}
                        </tbody>
                    </table>
                </div>
                <p className={styles.emptyState} id="empty-list" hidden={workbooks.length > 0}>No surveys uploaded yet.</p>
            </main>
        </>
    );
}
